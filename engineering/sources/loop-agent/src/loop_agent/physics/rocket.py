"""ロケットシステム設計 物理コア（Phase 6a: 質量/ΔVクロージャ）。

■ モデルの適用範囲（重要 — docs/06 敵対的検証 P-1 を必読）
第一次近似モデルである。前提:
  - ツィオルコフスキーの式 + 一定Isp（初段の海面〜真空変化は「平均Isp」で代表）
  - 構造係数 eps = m_dry/(m_dry+m_prop) は段規模に依らず一定（スケール則未考慮）
  - 上昇損失（重力/空力/操舵）は定数推定値（軌道積分は6cで置換すること）
→ 段構成の**相対比較・クロージャループの骨格**には妥当。
→ 絶対値での機体コミット・要求確定に単独使用してはならない。

単位系: SI（m, kg, s, N）。Ispのみ慣例に従い秒 [s]。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

G0 = 9.80665  # 標準重力加速度 [m/s^2]

# 上昇損失の定数推定値 [m/s]（第一次近似。6cで軌道積分に置換）
DEFAULT_LOSSES = {"gravity": 1200.0, "drag": 120.0, "steering": 80.0}


@dataclass
class Stage:
    name: str
    isp_s: float                 # 代表比推力 [s]（初段は上昇平均値を与えること）
    eps: float                   # 構造係数 m_dry/(m_dry+m_prop)。典型 0.05-0.15
    thrust_N: float | None = None  # 段合計推力（TWR検査用。省略可）

    def __post_init__(self):
        if not (0.0 < self.eps < 1.0):
            raise ValueError(f"eps must be in (0,1): {self.eps}")
        if self.isp_s <= 0:
            raise ValueError(f"isp_s must be positive: {self.isp_s}")


@dataclass
class StageResult:
    name: str
    dv_m_s: float
    m_prop_kg: float
    m_dry_kg: float
    m0_kg: float                 # この段点火時の全備質量（上段+ペイロード込み）
    feasible: bool
    closure_k: float             # (R-1)*eps/(1-eps)。>=1 でクロージャ不成立
    twr: float | None = None     # 点火時推重比（thrust指定時のみ）


@dataclass
class VehicleResult:
    stages: list[StageResult]    # index 0 = 最下段
    payload_kg: float
    glow_kg: float               # Gross Lift-Off Weight（質量）[kg]
    dv_total_m_s: float
    feasible: bool
    infeasibility: float = 0.0   # 不成立度合い（最適化のペナルティ用）Σmax(0, k-1)

    def to_dict(self) -> dict:
        return {
            "payload_kg": self.payload_kg, "glow_kg": self.glow_kg,
            "dv_total_m_s": self.dv_total_m_s, "feasible": self.feasible,
            "stages": [vars(s) for s in self.stages],
        }


def dv_from_masses(isp_s: float, m0: float, mf: float) -> float:
    """ツィオルコフスキーの式。"""
    if not (m0 > mf > 0):
        raise ValueError("require m0 > mf > 0")
    return G0 * isp_s * math.log(m0 / mf)


def size_stage(dv_m_s: float, stage: Stage, m_upper_kg: float) -> StageResult:
    """要求ΔVと上載質量から段の推進剤・乾燥質量を解析的に求める。

    導出: R=exp(dv/(g0*Isp)), e'=eps/(1-eps) として
      m_prop = (R-1)*m_upper / (1 - (R-1)*e'),  m_dry = e' * m_prop
    (R-1)*e' >= 1 のとき、そのΔVはこの段では物理的に達成不能（クロージャ不成立）。
    """
    x = dv_m_s / (G0 * stage.isp_s)
    if x > 50:  # exp overflow ガード（現実の機体で到達しない領域）
        return StageResult(stage.name, dv_m_s, math.inf, math.inf, math.inf,
                           False, math.inf)
    r = math.exp(x)
    e_prime = stage.eps / (1.0 - stage.eps)
    k = (r - 1.0) * e_prime
    if k >= 1.0:
        return StageResult(stage.name, dv_m_s, math.inf, math.inf, math.inf, False, k)

    m_prop = (r - 1.0) * m_upper_kg / (1.0 - k)
    m_dry = e_prime * m_prop
    m0 = m_upper_kg + m_dry + m_prop
    twr = stage.thrust_N / (m0 * G0) if stage.thrust_N else None
    return StageResult(stage.name, dv_m_s, m_prop, m_dry, m0, True, k, twr)


def size_vehicle(stages: list[Stage], dv_split_m_s: list[float],
                 payload_kg: float) -> VehicleResult:
    """多段サイジング。上段から下段へ積み上げる（stages[0]=最下段）。"""
    if len(stages) != len(dv_split_m_s):
        raise ValueError("stages と dv_split の長さが一致しない")
    results: list[StageResult] = []
    m_upper = payload_kg
    infeas = 0.0
    for stage, dv in zip(reversed(stages), reversed(dv_split_m_s)):
        sr = size_stage(dv, stage, m_upper)
        results.insert(0, sr)
        infeas += max(0.0, sr.closure_k - 1.0) if math.isfinite(sr.closure_k) else 10.0
        if not sr.feasible:
            return VehicleResult(results, payload_kg, math.inf,
                                 sum(dv_split_m_s), False, infeas)
        m_upper = sr.m0_kg
    return VehicleResult(results, payload_kg, results[0].m0_kg,
                         sum(dv_split_m_s), True, 0.0)


def mission_dv(orbit_dv_m_s: float, losses: dict[str, float] | None = None) -> float:
    """軌道投入ΔV + 上昇損失（定数推定）。6cで軌道積分に置換すること。"""
    loss = losses if losses is not None else DEFAULT_LOSSES
    return orbit_dv_m_s + sum(loss.values())


def optimize_dv_split(stages: list[Stage], payload_kg: float, dv_total_m_s: float,
                      n_restarts: int = 4) -> list[float]:
    """GLOW最小化のΔV配分探索（SLSQP・多スタートで局所解を緩和）。

    注意: それでも大域最適の保証はない（docs/06 P-2）。結果は必ず
    feasibility と均等割との比較で妥当性確認すること。
    """
    n = len(stages)
    if n == 1:
        return [dv_total_m_s]
    from scipy.optimize import minimize  # 遅延import

    def objective(f):
        v = size_vehicle(stages, [fi * dv_total_m_s for fi in f], payload_kg)
        return v.glow_kg if v.feasible else 1e9 * (1.0 + v.infeasibility)

    best_x, best_val = None, math.inf
    starts = [[1.0 / n] * n]
    for i in range(n_restarts - 1):  # 偏らせた初期点を追加
        w = [1.0 + 0.6 * ((i + j) % n == j) for j in range(n)]
        starts.append([wi / sum(w) for wi in w])
    for x0 in starts:
        res = minimize(objective, x0, method="SLSQP",
                       bounds=[(0.05, 0.95)] * n,
                       constraints=({"type": "eq", "fun": lambda f: sum(f) - 1.0},))
        if res.fun < best_val:
            best_val, best_x = res.fun, res.x
    return [float(fi) * dv_total_m_s for fi in best_x]
