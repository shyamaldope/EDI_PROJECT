import React, { useState, useEffect } from 'react';
import { BarChart3, Sliders, TrendingUp, DollarSign, Users, Target, ShieldCheck, MapPin } from 'lucide-react';
import { api } from '../api/client';

export default function AuthorityDashboard() {
  const [incomeCeiling, setIncomeCeiling] = useState(250000);
  const [landCeiling, setLandCeiling] = useState(5.0);
  const [selectedScheme, setSelectedScheme] = useState('pm_kisan');
  const [simulation, setSimulation] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Goal-seek state
  const [targetBudget, setTargetBudget] = useState(150000);
  const [goalSeekResult, setGoalSeekResult] = useState(null);
  const [seeking, setSeeking] = useState(false);

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const data = await api.simulateWhatIf({
        scheme_id: selectedScheme,
        income_ceiling: incomeCeiling,
        land_ceiling: landCeiling
      });
      setSimulation(data);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [incomeCeiling, landCeiling, selectedScheme]);

  const handleGoalSeek = async () => {
    setSeeking(true);
    try {
      const res = await api.goalSeek({
        scheme_id: selectedScheme,
        target_budget: targetBudget
      });
      setGoalSeekResult(res);
      if (res.recommended_income_cutoff) {
        setIncomeCeiling(res.recommended_income_cutoff);
      }
    } catch (err) {
      console.error('Goal-seek failed:', err);
    } finally {
      setSeeking(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-govblue-800" />
          <span>Policy Digital Twin & Inverse Budget Goal-Seek Optimizer</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Sandbox for District Collectors and Department Secretaries. Empirically test parameter adjustments
          across the active population before gazette notification, or solve for optimal cutoffs given budget targets.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: What-If Parameter Controls & Goal-Seek */}
        <div className="space-y-6">
          {/* Forward Sliders */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-govblue-800" />
                <span>Policy Parameter Levers</span>
              </h3>
              <span className="text-[10px] bg-blue-50 text-govblue-800 font-bold px-2 py-0.5 rounded">
                WHAT-IF
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Welfare Scheme:</label>
              <select
                value={selectedScheme}
                onChange={(e) => setSelectedScheme(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium"
              >
                <option value="pm_kisan">PM-KISAN Samman Nidhi (Agri)</option>
                <option value="mahadbt_post_matric_obc">MahaDBT Post-Matric OBC Scholarship</option>
                <option value="ladki_bahin">Mukhyamantri Majhi Ladki Bahin Yojana</option>
                <option value="maha_krishi_urja_solar">Maha Krishi Urja Solar Pump</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Annual Family Income Ceiling:</span>
                <span className="text-govblue-800 font-bold font-mono">₹{Number(incomeCeiling).toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="50000"
                max="800000"
                step="10000"
                value={incomeCeiling}
                onChange={(e) => setIncomeCeiling(Number(e.target.value))}
                className="w-full accent-govblue-800 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                <span>₹50K</span>
                <span>₹400K</span>
                <span>₹800K</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Landholding Limit (Acres):</span>
                <span className="text-govblue-800 font-bold font-mono">{landCeiling} Acres</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="10.0"
                step="0.5"
                value={landCeiling}
                onChange={(e) => setLandCeiling(Number(e.target.value))}
                className="w-full accent-govblue-800 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                <span>1.0 Acre</span>
                <span>5.0 Acres</span>
                <span>10.0 Acres</span>
              </div>
            </div>
          </div>

          {/* Inverse Goal-Seek Box */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Target className="h-4 w-4 text-govorange-500" />
                <span>Inverse Budget Goal-Seek</span>
              </h3>
              <span className="text-[10px] bg-orange-50 text-govorange-600 font-bold px-2 py-0.5 rounded">
                OPTIMIZER
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Specify your department's expenditure budget. The optimizer solves for the exact income threshold to maximize coverage.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Available Target Budget (₹):</label>
              <input
                type="number"
                value={targetBudget}
                onChange={(e) => setTargetBudget(Number(e.target.value))}
                step="10000"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono font-bold"
              />
            </div>

            <button
              onClick={handleGoalSeek}
              disabled={seeking}
              className="w-full py-2 bg-govorange-500 hover:bg-govorange-600 text-white rounded-lg text-xs font-bold shadow transition-all"
            >
              {seeking ? 'Solving Optimal Cutoff...' : 'Calculate Optimal Income Cutoff'}
            </button>

            {goalSeekResult && (
              <div className="p-3 bg-orange-50 rounded-xl border border-orange-200 text-xs space-y-1">
                <span className="font-bold text-govorange-700 block">Optimizer Recommendation:</span>
                <div>Optimal Income Ceiling: <b className="font-mono text-slate-800">₹{goalSeekResult.recommended_income_cutoff.toLocaleString()}</b></div>
                <div>Resulting Beneficiaries: <b className="font-mono text-slate-800">{goalSeekResult.resulting_beneficiaries} citizens</b></div>
                <div>Budget Utilization: <b className="font-mono text-emerald-700">{goalSeekResult.budget_utilization_pct}%</b></div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Real-Time Simulation Results */}
        <div className="lg:col-span-2 space-y-6">
          {simulation ? (
            <>
              {/* Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1 font-semibold">
                    <span>Beneficiary Coverage</span>
                    <Users className="h-4 w-4 text-govblue-800" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {simulation.scenario.beneficiary_count}
                    <span className="text-xs font-medium text-slate-500 ml-1">citizens</span>
                  </div>
                  <div className="text-xs text-emerald-600 font-bold mt-1">
                    +{simulation.impact.net_new_beneficiaries} ({simulation.impact.percentage_expansion}% expansion)
                  </div>
                </div>

                <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1 font-semibold">
                    <span>Scenario State Budget</span>
                    <DollarSign className="h-4 w-4 text-emerald-600" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 mt-1 font-mono">
                    ₹{simulation.scenario.budget_required.toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-500 font-medium mt-1">
                    Baseline: ₹{simulation.baseline.budget_required.toLocaleString()}
                  </div>
                </div>

                <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between text-slate-500 text-xs mb-1 font-semibold">
                    <span>Net Budgetary Impact</span>
                    <TrendingUp className="h-4 w-4 text-govorange-500" />
                  </div>
                  <div className="text-2xl font-black text-govorange-600 mt-1 font-mono">
                    +₹{simulation.impact.budget_increase.toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-500 font-medium mt-1">
                    At ₹{simulation.benefit_per_citizen.toLocaleString()} per beneficiary
                  </div>
                </div>
              </div>

              {/* Demographic Distribution */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {/* By District */}
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-govblue-800" />
                    <span>Beneficiary Distribution by District</span>
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(simulation.demographic_breakdown.by_district || {}).map(([dist, count]) => (
                      <div key={dist} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-slate-700">{dist}</span>
                          <span className="font-mono text-slate-600">{count} citizens</span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-govblue-800 h-full rounded-full"
                            style={{ width: `${Math.min(100, (count / simulation.scenario.beneficiary_count) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* By Caste */}
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Beneficiary Distribution by Category</span>
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(simulation.demographic_breakdown.by_caste || {}).map(([caste, count]) => (
                      <div key={caste} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-slate-700">{caste}</span>
                          <span className="font-mono text-slate-600">{count} citizens</span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-600 h-full rounded-full"
                            style={{ width: `${Math.min(100, (count / simulation.scenario.beneficiary_count) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 text-slate-400">
              Running Policy Twin Simulation...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
