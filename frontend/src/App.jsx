import { useState, useRef, useCallback, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid, ReferenceLine
} from "recharts";

const API = import.meta.env.VITE_API_URL || "/api";

// ─── Helpers ─────────────────────────────────────────────────
const fmt   = (n) => Math.round(n ?? 0);
const fmtg  = (n) => (n ?? 0).toFixed(1) + "g";
const today = () => new Date().toISOString().split("T")[0];

const MACRO_COLORS = { protein:"#4ade80", carbs:"#60a5fa", fat:"#f59e0b", fiber:"#a78bfa" };
const GOAL_OPTIONS = [
  { key:"weight_loss",  label:"🔥 Weight Loss",  cal:1500 },
  { key:"muscle_gain",  label:"💪 Muscle Gain",   cal:2800 },
  { key:"maintenance",  label:"⚖️  Maintenance",  cal:2000 },
  { key:"keto",         label:"🥑 Keto",          cal:1800 },
];

// ─── Macro Ring ───────────────────────────────────────────────
const MacroRing = ({ protein=0, carbs=0, fat=0 }) => {
  const total = protein * 4 + carbs * 4 + fat * 9 || 1;
  const data = [
    { name:"Protein", value: protein*4, color:"#4ade80" },
    { name:"Carbs",   value: carbs*4,   color:"#60a5fa" },
    { name:"Fat",     value: fat*9,     color:"#f59e0b" },
  ];
  return (
    <PieChart width={120} height={120}>
      <Pie data={data} dataKey="value" cx={60} cy={60}
        innerRadius={36} outerRadius={54} paddingAngle={2} startAngle={90} endAngle={-270}>
        {data.map((d,i) => <Cell key={i} fill={d.color} />)}
      </Pie>
    </PieChart>
  );
};

// ─── Calorie Arc ─────────────────────────────────────────────
const CalorieArc = ({ consumed, target }) => {
  const pct = Math.min(consumed / target, 1);
  const r = 70, cx = 90, cy = 90, stroke = 14;
  const circ = Math.PI * r;
  const dash  = pct * circ;
  const color = pct > 1 ? "#f87171" : pct > 0.8 ? "#f59e0b" : "#4ade80";
  return (
    <svg width={180} height={100} viewBox="0 0 180 100">
      <path d={`M ${cx-r},${cy} A ${r},${r} 0 0,1 ${cx+r},${cy}`}
        fill="none" stroke="#1e293b" strokeWidth={stroke} strokeLinecap="round"/>
      <path d={`M ${cx-r},${cy} A ${r},${r} 0 0,1 ${cx+r},${cy}`}
        fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        style={{transition:"stroke-dasharray 1s ease"}}/>
      <text x={cx} y={cy-12} textAnchor="middle" fill="#f1f5f9" fontSize={22} fontWeight={800}>{fmt(consumed)}</text>
      <text x={cx} y={cy+4}  textAnchor="middle" fill="#64748b" fontSize={11}>of {fmt(target)} kcal</text>
    </svg>
  );
};

// ─── Macro Bar ────────────────────────────────────────────────
const MacroBar = ({ label, value, max, color }) => {
  const pct = Math.min((value / Math.max(max,1)) * 100, 100);
  return (
    <div style={{marginBottom:10}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
        <span style={{color:"#94a3b8",fontSize:12}}>{label}</span>
        <span style={{color,fontSize:12,fontWeight:700}}>{fmtg(value)}</span>
      </div>
      <div style={{background:"#1e293b",borderRadius:999,height:7,overflow:"hidden"}}>
        <div style={{width:`${pct}%`,height:"100%",background:color,borderRadius:999,
          transition:"width 1s ease",boxShadow:`0 0 6px ${color}66`}}/>
      </div>
    </div>
  );
};

// ─── Confidence Bar ───────────────────────────────────────────
const ConfBar = ({value, color="#4ade80"}) => (
  <div style={{background:"#1e293b",borderRadius:999,height:6,overflow:"hidden",flex:1}}>
    <div style={{width:`${value}%`,height:"100%",background:color,borderRadius:999,transition:"width 0.8s ease"}}/>
  </div>
);

// ─────────────────────────────────────────────────────────────
// SCAN TAB
// ─────────────────────────────────────────────────────────────
const ScanTab = ({ onLog, todayTotals, goal }) => {
  const [imgSrc, setImgSrc] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [portion, setPortion] = useState(150);
  const [logged, setLogged] = useState(false);
  const fileRef = useRef();
  const cameraRef = useRef();

  const analyze = async (file) => {
    if (!file?.type.startsWith("image/")) return;
    setLoading(true); setResult(null); setErr(null); setLogged(false);
    setImgSrc(URL.createObjectURL(file));
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/predict?portion_g=${portion}`, { method:"POST", body:fd });
      if (!res.ok) throw new Error(res.status);
      setResult(await res.json());
    } catch {
      setErr("Cannot reach API. Make sure the backend is running.");
    } finally { setLoading(false); }
  };

  const handleLog = async () => {
    if (!result) return;
    const body = {
      food_class: result.food_class, food_name: result.food_name,
      serving_g: result.serving_g,
      calories: result.totals.calories, protein: result.totals.protein,
      carbs: result.totals.carbs, fat: result.totals.fat, fiber: result.totals.fiber,
      timestamp: new Date().toISOString()
    };
    await fetch(`${API}/log`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    onLog(body);
    setLogged(true);
  };

  const re = result;
  return (
    <div>
      <h2 style={{fontSize:22,fontWeight:800,margin:"0 0 18px"}}>📸 Scan Food</h2>

      {/* Portion slider */}
      <div style={{background:"#0f172a",borderRadius:14,padding:"14px 18px",marginBottom:16,border:"1px solid #1e293b"}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
          <span style={{color:"#94a3b8",fontSize:13}}>Portion size</span>
          <span style={{color:"#4ade80",fontWeight:700,fontSize:13}}>{portion}g</span>
        </div>
        <input type="range" min={50} max={600} step={10} value={portion}
          onChange={e=>setPortion(Number(e.target.value))}
          style={{width:"100%",accentColor:"#4ade80"}}/>
        <div style={{display:"flex",justifyContent:"space-between"}}>
          <span style={{color:"#334155",fontSize:11}}>50g</span>
          <span style={{color:"#334155",fontSize:11}}>600g</span>
        </div>
      </div>

      {/* Upload zone */}
      <div
        onClick={()=>!loading && fileRef.current.click()}
        onDragOver={e=>{e.preventDefault();setDragging(true)}}
        onDragLeave={()=>setDragging(false)}
        onDrop={e=>{e.preventDefault();setDragging(false);analyze(e.dataTransfer.files[0])}}
        style={{border:`2px dashed ${dragging?"#4ade80":"#334155"}`,borderRadius:18,
          padding:"40px 20px",textAlign:"center",cursor:loading?"wait":"pointer",
          background:dragging?"#0f2818":"#0f172a",transition:"all 0.25s",marginBottom:12}}>
        {imgSrc && !loading
          ? <img src={imgSrc} alt="" style={{width:"100%",maxHeight:220,objectFit:"cover",borderRadius:12,marginBottom:12}}/>
          : <div style={{fontSize:52,marginBottom:10}}>{loading?"⏳":"🍽️"}</div>}
        <p style={{color:"#e2e8f0",fontWeight:700,margin:"0 0 4px",fontSize:16}}>
          {loading ? "Identifying food…" : imgSrc ? "Tap to scan again" : "Drop a food photo here"}
        </p>
        <p style={{color:"#64748b",fontSize:12,margin:0}}>
          {loading ? "AI analysing…" : "or tap to upload · JPEG · PNG · WebP"}
        </p>
        {loading && <div style={{width:38,height:38,border:"3px solid #1e293b",borderTop:"3px solid #4ade80",
          borderRadius:"50%",animation:"spin 0.9s linear infinite",margin:"14px auto 0"}}/>}
        <input ref={fileRef} type="file" accept="image/*" hidden onChange={e=>analyze(e.target.files[0])}/>
      </div>

      {/* Camera button (mobile) */}
      <button onClick={()=>cameraRef.current.click()}
        style={{width:"100%",background:"#0f172a",border:"1px solid #334155",color:"#94a3b8",
          padding:"12px",borderRadius:12,fontSize:14,cursor:"pointer",marginBottom:16}}>
        📷 Take Photo
        <input ref={cameraRef} type="file" accept="image/*" capture="environment"
          hidden onChange={e=>analyze(e.target.files[0])}/>
      </button>

      {err && <div style={{background:"#4c0519",borderRadius:12,padding:"12px 16px",border:"1px solid #f87171",marginBottom:12}}>
        <p style={{color:"#fca5a5",margin:0,fontSize:13}}>⚠️ {err}</p></div>}

      {/* Result card */}
      {re && !loading && (
        <div style={{background:"#0f172a",borderRadius:18,border:"1px solid #1e293b",overflow:"hidden",animation:"fade 0.4s ease"}}>
          {/* Header */}
          <div style={{padding:"18px 20px",borderBottom:"1px solid #1e293b",
            background:"linear-gradient(135deg,#14532d22,transparent)"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
              <div>
                <p style={{color:"#4ade80",fontSize:11,margin:"0 0 4px",textTransform:"uppercase",letterSpacing:"0.1em"}}>{re.category}</p>
                <h3 style={{color:"#f1f5f9",margin:"0 0 2px",fontSize:20,fontWeight:800}}>{re.food_name}</h3>
                <p style={{color:"#64748b",margin:0,fontSize:12}}>{re.serving_g}g · {re.confidence}% confidence</p>
              </div>
              <div style={{textAlign:"right"}}>
                <div style={{color:"#4ade80",fontSize:32,fontWeight:800}}>{fmt(re.totals.calories)}</div>
                <div style={{color:"#64748b",fontSize:12}}>kcal</div>
              </div>
            </div>
          </div>

          {/* Macros */}
          <div style={{padding:"16px 20px",borderBottom:"1px solid #1e293b"}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:10,marginBottom:14,textAlign:"center"}}>
              {[
                {label:"Protein",val:re.totals.protein,color:"#4ade80"},
                {label:"Carbs",  val:re.totals.carbs,  color:"#60a5fa"},
                {label:"Fat",    val:re.totals.fat,    color:"#f59e0b"},
                {label:"Fiber",  val:re.totals.fiber,  color:"#a78bfa"},
              ].map(m=>(
                <div key={m.label} style={{background:"#1e293b",borderRadius:10,padding:"10px 6px"}}>
                  <div style={{color:m.color,fontSize:16,fontWeight:800}}>{fmtg(m.val)}</div>
                  <div style={{color:"#64748b",fontSize:11,marginTop:2}}>{m.label}</div>
                </div>
              ))}
            </div>
            <p style={{color:"#475569",fontSize:11,margin:"0 0 6px"}}>per 100g · Calories: {fmt(re.per_100g.calories)} | Protein: {fmtg(re.per_100g.protein)} | Carbs: {fmtg(re.per_100g.carbs)} | Fat: {fmtg(re.per_100g.fat)}</p>
          </div>

          {/* Top 5 */}
          <div style={{padding:"14px 20px",borderBottom:"1px solid #1e293b"}}>
            <p style={{color:"#64748b",fontSize:11,margin:"0 0 10px",textTransform:"uppercase",letterSpacing:"0.08em"}}>Other possibilities</p>
            {re.top5?.slice(1).map((t,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:10,marginBottom:7}}>
                <span style={{color:"#475569",fontSize:12,minWidth:140,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                  {t.class.replace(/_/g," ")}
                </span>
                <ConfBar value={t.confidence*100} color="#334155"/>
                <span style={{color:"#475569",fontSize:11,minWidth:36,textAlign:"right"}}>{(t.confidence*100).toFixed(0)}%</span>
              </div>
            ))}
          </div>

          {/* Log button */}
          <div style={{padding:"16px 20px"}}>
            <button onClick={handleLog} disabled={logged}
              style={{width:"100%",background:logged?"#064e3b":"#16a34a",border:"none",
                color:"#fff",padding:"14px",borderRadius:12,fontSize:15,fontWeight:700,
                cursor:logged?"default":"pointer",transition:"all 0.2s"}}>
              {logged ? "✅ Logged to today's diary" : "➕ Add to Today's Log"}
            </button>
            {re.demo_mode && <p style={{color:"#ca8a04",fontSize:11,margin:"8px 0 0",textAlign:"center"}}>
              ⚡ Demo mode — results are simulated
            </p>}
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// DIARY TAB
// ─────────────────────────────────────────────────────────────
const DiaryTab = ({ log, todayTotals, goal, onDelete }) => {
  const remaining = (goal?.daily_target || 2000) - (todayTotals?.calories || 0);
  return (
    <div>
      <h2 style={{fontSize:22,fontWeight:800,margin:"0 0 18px"}}>📋 Today's Diary</h2>

      {/* Calorie arc */}
      <div style={{background:"#0f172a",borderRadius:18,border:"1px solid #1e293b",padding:"20px",marginBottom:16,textAlign:"center"}}>
        <CalorieArc consumed={todayTotals?.calories||0} target={goal?.daily_target||2000}/>
        <div style={{display:"flex",justifyContent:"center",gap:24,marginTop:8}}>
          <div style={{textAlign:"center"}}>
            <div style={{color:"#60a5fa",fontSize:13,fontWeight:700}}>{fmt(goal?.daily_target||2000)}</div>
            <div style={{color:"#475569",fontSize:11}}>Target</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{color:"#4ade80",fontSize:13,fontWeight:700}}>{fmt(todayTotals?.calories||0)}</div>
            <div style={{color:"#475569",fontSize:11}}>Eaten</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{color:remaining<0?"#f87171":"#f59e0b",fontSize:13,fontWeight:700}}>{fmt(Math.abs(remaining))}</div>
            <div style={{color:"#475569",fontSize:11}}>{remaining<0?"Over":"Left"}</div>
          </div>
        </div>
      </div>

      {/* Macro bars */}
      <div style={{background:"#0f172a",borderRadius:18,border:"1px solid #1e293b",padding:"16px 20px",marginBottom:16}}>
        <p style={{color:"#64748b",fontSize:12,margin:"0 0 12px",textTransform:"uppercase",letterSpacing:"0.08em"}}>Macros today</p>
        <MacroBar label="Protein" value={todayTotals?.protein||0} max={goal?.daily_target/4||50}  color="#4ade80"/>
        <MacroBar label="Carbs"   value={todayTotals?.carbs||0}   max={goal?.daily_target/4||120} color="#60a5fa"/>
        <MacroBar label="Fat"     value={todayTotals?.fat||0}     max={goal?.daily_target/9||60}  color="#f59e0b"/>
        <MacroBar label="Fiber"   value={todayTotals?.fiber||0}   max={35}                        color="#a78bfa"/>
      </div>

      {/* Meal log list */}
      {log.length === 0
        ? <div style={{textAlign:"center",padding:"50px 0",color:"#475569"}}>
            <p style={{fontSize:40,margin:"0 0 10px"}}>🍽️</p>
            <p>No meals logged yet. Scan your food!</p>
          </div>
        : log.map((e,i)=>(
          <div key={i} style={{background:"#0f172a",borderRadius:14,border:"1px solid #1e293b",
            padding:"14px 18px",marginBottom:10,display:"flex",alignItems:"center",gap:12}}>
            <div style={{flex:1}}>
              <div style={{display:"flex",justifyContent:"space-between"}}>
                <span style={{color:"#f1f5f9",fontWeight:700,fontSize:14}}>{e.food_name}</span>
                <span style={{color:"#4ade80",fontWeight:800,fontSize:15}}>{fmt(e.calories)} kcal</span>
              </div>
              <div style={{color:"#475569",fontSize:12,marginTop:3}}>
                {e.serving_g}g · P: {fmtg(e.protein)} · C: {fmtg(e.carbs)} · F: {fmtg(e.fat)}
              </div>
              <div style={{color:"#334155",fontSize:11,marginTop:2}}>
                {new Date(e.timestamp).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}
              </div>
            </div>
            <button onClick={()=>onDelete(i)}
              style={{background:"#1e293b",border:"1px solid #334155",color:"#ef4444",
                width:32,height:32,borderRadius:8,cursor:"pointer",fontSize:16,flexShrink:0}}>×</button>
          </div>
        ))
      }
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// DASHBOARD TAB
// ─────────────────────────────────────────────────────────────
const DashboardTab = ({ todayTotals, goal, log }) => {
  const weekly = [
    {day:"Mon",calories:1820,target:2000},{day:"Tue",calories:2150,target:2000},
    {day:"Wed",calories:1760,target:2000},{day:"Thu",calories:2340,target:2000},
    {day:"Fri",calories:1980,target:2000},{day:"Sat",calories:2100,target:2000},
    {day:"Sun",calories:todayTotals?.calories||1540,target:2000},
  ];
  const macroData = [
    {name:"Protein",value:Math.max(todayTotals?.protein||0,1),color:"#4ade80"},
    {name:"Carbs",  value:Math.max(todayTotals?.carbs||0,1),  color:"#60a5fa"},
    {name:"Fat",    value:Math.max(todayTotals?.fat||0,1),    color:"#f59e0b"},
  ];
  const stats = [
    {icon:"🔥",label:"Today",value:`${fmt(todayTotals?.calories||0)} kcal`,color:"#f87171"},
    {icon:"🎯",label:"Target",value:`${fmt(goal?.daily_target||2000)} kcal`,color:"#60a5fa"},
    {icon:"🍽️",label:"Meals",value:log.length,color:"#4ade80"},
    {icon:"📅",label:"Streak",value:"7 days",color:"#a78bfa"},
  ];
  return (
    <div>
      <h2 style={{fontSize:22,fontWeight:800,margin:"0 0 18px"}}>📊 Dashboard</h2>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:16}}>
        {stats.map((s,i)=>(
          <div key={i} style={{background:"#0f172a",borderRadius:14,border:"1px solid #1e293b",padding:"16px 18px"}}>
            <div style={{fontSize:24,marginBottom:6}}>{s.icon}</div>
            <div style={{color:s.color,fontSize:20,fontWeight:800}}>{s.value}</div>
            <div style={{color:"#475569",fontSize:12,marginTop:3}}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Weekly chart */}
      <div style={{background:"#0f172a",borderRadius:18,border:"1px solid #1e293b",padding:"18px",marginBottom:16}}>
        <p style={{color:"#94a3b8",fontSize:13,fontWeight:600,margin:"0 0 14px"}}>📈 Weekly Calories</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={weekly} barSize={20}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b"/>
            <XAxis dataKey="day" stroke="#475569" tick={{fontSize:11}}/>
            <YAxis stroke="#475569" tick={{fontSize:10}} domain={[0,3000]}/>
            <Tooltip contentStyle={{background:"#1e293b",border:"none",borderRadius:8,color:"#e2e8f0",fontSize:12}}/>
            <ReferenceLine y={goal?.daily_target||2000} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1.5}/>
            <Bar dataKey="calories" radius={[6,6,0,0]}
              fill="#4ade80"
              label={false}
            />
          </BarChart>
        </ResponsiveContainer>
        <p style={{color:"#334155",fontSize:11,margin:"6px 0 0",textAlign:"center"}}>— target line</p>
      </div>

      {/* Macro pie */}
      <div style={{background:"#0f172a",borderRadius:18,border:"1px solid #1e293b",padding:"18px",marginBottom:16}}>
        <p style={{color:"#94a3b8",fontSize:13,fontWeight:600,margin:"0 0 14px"}}>🥗 Today's Macro Split</p>
        <div style={{display:"flex",alignItems:"center",gap:16}}>
          <PieChart width={130} height={130}>
            <Pie data={macroData} dataKey="value" cx={65} cy={65}
              innerRadius={38} outerRadius={58} paddingAngle={3}>
              {macroData.map((d,i)=><Cell key={i} fill={d.color}/>)}
            </Pie>
          </PieChart>
          <div style={{flex:1}}>
            {macroData.map((m,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}>
                <div style={{width:10,height:10,borderRadius:2,background:m.color,flexShrink:0}}/>
                <span style={{color:"#94a3b8",fontSize:13,flex:1}}>{m.name}</span>
                <span style={{color:m.color,fontWeight:700,fontSize:13}}>{fmtg(m.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// SUGGESTIONS TAB
// ─────────────────────────────────────────────────────────────
const SuggestionsTab = ({ goal, setGoal }) => {
  const [suggestions, setSuggestions] = useState([]);
  const current = GOAL_OPTIONS.find(g=>g.key===goal.goal) || GOAL_OPTIONS[2];

  useEffect(()=>{
    fetch(`${API}/suggestions?goal=${goal.goal}`)
      .then(r=>r.json())
      .then(d=>setSuggestions(d.suggestions||[]))
      .catch(()=>setSuggestions([]));
  },[goal.goal]);

  return (
    <div>
      <h2 style={{fontSize:22,fontWeight:800,margin:"0 0 18px"}}>🎯 My Goal</h2>

      {/* Goal picker */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:20}}>
        {GOAL_OPTIONS.map(g=>(
          <button key={g.key} onClick={()=>setGoal({goal:g.key,daily_target:g.cal})}
            style={{background:goal.goal===g.key?"#14532d":"#0f172a",
              border:`1px solid ${goal.goal===g.key?"#4ade80":"#1e293b"}`,
              color:goal.goal===g.key?"#4ade80":"#94a3b8",
              padding:"14px 10px",borderRadius:14,cursor:"pointer",
              fontSize:13,fontWeight:600,transition:"all 0.2s",textAlign:"center"}}>
            <div style={{fontSize:20,marginBottom:4}}>{g.label.split(" ")[0]}</div>
            {g.label.split(" ").slice(1).join(" ")}
            <div style={{color:"#475569",fontSize:11,marginTop:4,fontWeight:400}}>{g.cal} kcal/day</div>
          </button>
        ))}
      </div>

      {/* Daily target */}
      <div style={{background:"#0f172a",borderRadius:14,border:"1px solid #1e293b",padding:"16px 20px",marginBottom:20}}>
        <p style={{color:"#64748b",fontSize:12,margin:"0 0 8px",textTransform:"uppercase",letterSpacing:"0.08em"}}>Daily Target</p>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <span style={{color:"#4ade80",fontSize:32,fontWeight:800}}>{fmt(goal.daily_target)}</span>
          <span style={{color:"#475569"}}>kcal / day</span>
        </div>
      </div>

      {/* Meal suggestions */}
      <p style={{color:"#94a3b8",fontSize:13,fontWeight:600,margin:"0 0 12px",textTransform:"uppercase",letterSpacing:"0.06em"}}>
        Recommended for {current.label}
      </p>
      {suggestions.map((s,i)=>{
        const n = Object.values({ ...Object.fromEntries(
          Object.entries(require ? {} : {})
        ) })[0];
        return (
          <div key={i} style={{background:"#0f172a",borderRadius:14,border:"1px solid #1e293b",
            padding:"14px 18px",marginBottom:10,display:"flex",alignItems:"center",gap:14}}>
            <div style={{flex:1}}>
              <div style={{color:"#f1f5f9",fontWeight:700,fontSize:14}}>{s.name}</div>
              <div style={{color:"#475569",fontSize:12,marginTop:3}}>{s.reason}</div>
            </div>
            <div style={{textAlign:"right"}}>
              <div style={{color:"#4ade80",fontWeight:800,fontSize:16}}>{s.calories}</div>
              <div style={{color:"#475569",fontSize:11}}>kcal</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("scan");
  const [log, setLog] = useState([]);
  const [goal, setGoal] = useState({goal:"maintenance",daily_target:2000});
  const [todayTotals, setTodayTotals] = useState({calories:0,protein:0,carbs:0,fat:0,fiber:0});

  const recalc = (entries) => {
    const t = {calories:0,protein:0,carbs:0,fat:0,fiber:0};
    entries.forEach(e=>{ for(const k of Object.keys(t)) t[k]+=e[k]||0; });
    setTodayTotals(t);
  };

  const onLog = (entry) => {
    const nl = [...log, entry];
    setLog(nl); recalc(nl);
  };

  const onDelete = (idx) => {
    const nl = log.filter((_,i)=>i!==idx);
    setLog(nl); recalc(nl);
  };

  const onGoalChange = async (g) => {
    setGoal(g);
    try { await fetch(`${API}/goal`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(g)}); }
    catch {}
  };

  const tabs = [
    {id:"scan",      icon:"📸", label:"Scan"},
    {id:"diary",     icon:"📋", label:"Diary"},
    {id:"dashboard", icon:"📊", label:"Stats"},
    {id:"goals",     icon:"🎯", label:"Goal"},
  ];

  return (
    <div style={{
      minHeight:"100vh", maxWidth:480, margin:"0 auto",
      background:"#020617", fontFamily:"'DM Sans','Segoe UI',sans-serif",
      color:"#f1f5f9", display:"flex", flexDirection:"column",
      position:"relative"
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
        @keyframes spin{to{transform:rotate(360deg)}}
        @keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
        *{box-sizing:border-box;margin:0;padding:0}
        input[type=range]{-webkit-appearance:none;height:6px;background:#1e293b;border-radius:3px}
        input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:#4ade80;cursor:pointer}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-thumb{background:#334155;border-radius:2px}
      `}</style>

      {/* Header */}
      <header style={{padding:"16px 20px 0",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:22}}>🍎</span>
          <span style={{fontWeight:800,fontSize:18}}>CalorieAI</span>
          <span style={{background:"#14532d",color:"#4ade80",fontSize:10,padding:"2px 8px",borderRadius:999,fontWeight:700,marginLeft:2}}>AI</span>
          <div style={{flex:1}}/>
          <div style={{background:"#0f172a",border:"1px solid #1e293b",borderRadius:20,padding:"4px 12px",fontSize:12,color:"#94a3b8"}}>
            🔥 {fmt(todayTotals.calories)} kcal
          </div>
        </div>
      </header>

      {/* Main content */}
      <main style={{flex:1,padding:"16px 20px 90px",overflowY:"auto",animation:"fade 0.3s ease"}}>
        {tab==="scan"      && <ScanTab onLog={onLog} todayTotals={todayTotals} goal={goal}/>}
        {tab==="diary"     && <DiaryTab log={log} todayTotals={todayTotals} goal={goal} onDelete={onDelete}/>}
        {tab==="dashboard" && <DashboardTab todayTotals={todayTotals} goal={goal} log={log}/>}
        {tab==="goals"     && <SuggestionsTab goal={goal} setGoal={onGoalChange}/>}
      </main>

      {/* Bottom nav */}
      <nav style={{
        position:"fixed", bottom:0, left:"50%", transform:"translateX(-50%)",
        width:"100%", maxWidth:480,
        background:"#0a0f1e", borderTop:"1px solid #1e293b",
        display:"grid", gridTemplateColumns:"repeat(4,1fr)",
        backdropFilter:"blur(16px)", zIndex:100
      }}>
        {tabs.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)} style={{
            background:"transparent", border:"none", cursor:"pointer",
            padding:"12px 4px", display:"flex", flexDirection:"column",
            alignItems:"center", gap:3,
            borderTop: tab===t.id ? "2px solid #4ade80" : "2px solid transparent",
            transition:"all 0.2s"
          }}>
            <span style={{fontSize:20}}>{t.icon}</span>
            <span style={{color:tab===t.id?"#4ade80":"#475569",fontSize:10,fontWeight:600}}>{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
