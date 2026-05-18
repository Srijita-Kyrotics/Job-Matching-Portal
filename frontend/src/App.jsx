import React, { useState, useRef } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Upload, CheckCircle, Search, ChevronDown, ChevronUp, User, LogIn } from 'lucide-react';

const MatchWheel = ({ score }) => {
  const percentage = Math.round((score || 0) * 100);
  const colorClass = percentage >= 80 ? 'high' : 'medium';
  return (
    <div className={`match-wheel ${colorClass}`}>
      <svg viewBox="0 0 36 36" className="circular-chart">
        <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
        <path className="circle" strokeDasharray={`${percentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
      </svg>
      <div className="percentage">{percentage}%</div>
    </div>
  );
};

const JobCard = ({ job }) => {
  const [expanded, setExpanded] = useState(false);
  const [showExplain, setShowExplain] = useState(false);
  const isPerfect = job.score >= 0.85;

  return (
    <motion.article 
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      className={`card job-card ${isPerfect ? 'perfect-match' : ''}`}
    >
      <div className="job-header">
        <div>
          <span style={{fontSize:'0.75rem', textTransform:'uppercase', color:'var(--accent-primary)', fontWeight:'bold'}}>{job.source}</span>
          <h3 className="job-title">{job.title}</h3>
          <div className="job-meta">{job.company} • {job.location}</div>
        </div>
        <MatchWheel score={job.score} />
      </div>

      <div className={`job-description ${expanded ? '' : 'collapsed'}`}>{job.description}</div>
      <button onClick={() => setExpanded(!expanded)} style={{background:'none', border:'none', color:'var(--accent-primary)', cursor:'pointer', marginBottom:'16px'}}>
        {expanded ? 'Show Less' : 'Read More'}
      </button>

      {job.match_breakdown && (
        <div style={{marginTop: '8px', borderTop: '1px solid var(--border-trans)', paddingTop: '16px'}}>
          <button onClick={() => setShowExplain(!showExplain)} style={{display:'flex', alignItems:'center', gap:'8px', background:'none', border:'none', color:'var(--text-secondary)', cursor:'pointer'}}>
            <Search size={16} /> Why this match? {showExplain ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
          </button>
          
          <AnimatePresence>
            {showExplain && (
              <motion.div initial={{height: 0, opacity: 0}} animate={{height: 'auto', opacity: 1}} exit={{height: 0, opacity: 0}} className="explain-drawer">
                <div style={{marginBottom:'12px'}}>
                  <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.85rem'}}><span>Semantic Similarity</span><span>{Math.round(job.match_breakdown.semantic_similarity*100)}%</span></div>
                  <div className="progress-bar"><div className="progress-fill" style={{width: `${job.match_breakdown.semantic_similarity*100}%`}}></div></div>
                </div>
                <div style={{marginBottom:'16px'}}>
                  <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.85rem'}}><span>Skill Requirements Met</span><span>{Math.round(job.match_breakdown.skill_overlap_ratio*100)}%</span></div>
                  <div className="progress-bar"><div className="progress-fill" style={{width: `${job.match_breakdown.skill_overlap_ratio*100}%`, background:'var(--color-success)'}}></div></div>
                </div>
                
                {job.match_breakdown.matched_skills?.length > 0 && (
                  <div>
                    <span style={{fontSize:'0.85rem', color:'var(--color-success)'}}>Matched Skills:</span>
                    <div className="skills-list">{job.match_breakdown.matched_skills.map(s => <span key={s} className="skill-pill matched">{s}</span>)}</div>
                  </div>
                )}
                {job.match_breakdown.missing_skills?.length > 0 && (
                  <div style={{marginTop:'12px'}}>
                    <span style={{fontSize:'0.85rem', color:'var(--color-danger)'}}>Missing Skills:</span>
                    <div className="skills-list">{job.match_breakdown.missing_skills.map(s => <span key={s} className="skill-pill missing">{s}</span>)}</div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      <div style={{marginTop: '24px'}}>
        <a href={job.url} target="_blank" rel="noreferrer" className="btn-apply">Apply Now ↗</a>
      </div>
    </motion.article>
  );
};const PipelineLoader = ({ elapsedTime }) => {
  let stage = "Analyzing your profile data...";
  if (elapsedTime > 2 && elapsedTime <= 5) {
    stage = "Generating high-dimensional semantic embeddings...";
  } else if (elapsedTime > 5 && elapsedTime <= 10) {
    stage = "Querying trusted job boards (LinkedIn & Internshala mock sources)...";
  } else if (elapsedTime > 10) {
    stage = "Running vector similarity matching & skill overlap engine...";
  }

  const showTimeoutWarning = elapsedTime >= 12;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      className="card loader-card"
      style={{ textAlign: 'center', padding: '48px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}
    >
      <div className="glowing-spinner-container">
        <div className="glowing-spinner"></div>
        <div className="spinner-center-icon">⚡</div>
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <h3 className="loader-title" style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>Discovering Matches</h3>
        <p className="loader-subtitle" style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginTop: '8px', minHeight: '40px', lineHeight: '1.5' }}>
          {stage}
        </p>
      </div>

      <div className="loader-timer" style={{ fontSize: '0.9rem', color: 'var(--accent-primary)', fontWeight: '700', background: 'rgba(59, 130, 246, 0.08)', padding: '6px 16px', borderRadius: '30px', border: '1px solid rgba(59, 130, 246, 0.15)' }}>
        Elapsed: {elapsedTime}s
      </div>

      {showTimeoutWarning && (
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="slow-response-alert"
          style={{
            marginTop: '8px',
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            background: 'rgba(245, 158, 11, 0.05)',
            color: '#fbd38d',
            fontSize: '0.85rem',
            lineHeight: '1.6',
            maxWidth: '420px',
            textAlign: 'left'
          }}
        >
          <strong style={{ color: 'var(--color-warning)', display: 'block', marginBottom: '4px' }}>⚠️ Processing taking longer than expected</strong>
          The pipeline is querying multiple databases and performing dense model embeddings. We are continuing to query and process, thank you for your patience!
        </motion.div>
      )}

      {/* Modern placeholder cards with pulse to keep interface interactive */}
      <div style={{ width: '100%', marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {[1, 2].map(i => (
          <div key={i} className="skeleton-placeholder" style={{ height: '76px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', display: 'flex', padding: '16px', alignItems: 'center' }}>
            <div className="skeleton" style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', flexShrink: 0, animation: 'pulse 1.8s infinite ease-in-out' }}></div>
            <div style={{ marginLeft: '16px', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="skeleton" style={{ width: '45%', height: '14px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', animation: 'pulse 1.8s infinite ease-in-out' }}></div>
              <div className="skeleton" style={{ width: '80%', height: '8px', borderRadius: '4px', background: 'rgba(255,255,255,0.03)', animation: 'pulse 1.8s infinite ease-in-out' }}></div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

const Dashboard = () => {
  const [form, setForm] = useState({ name: '', email: '', education: '', skills: '', experience: '', desired_roles: '', resume: null });
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const fileRef = useRef(null);
  const timerRef = useRef(null);

  React.useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const update = (field) => (e) => setForm(prev => ({...prev, [field]: field==='resume' ? e.target.files[0] : e.target.value}));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setElapsedTime(0);
    console.log("--- Frontend Submission Initiated ---");
    console.log("Form profile state:", form);
    
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    const controller = new AbortController();
    const signal = controller.signal;
    const timeoutId = setTimeout(() => {
      console.warn("Client-side timeout reached (30s). Aborting network request...");
      controller.abort();
    }, 30000);
    
    const data = new FormData();
    Object.entries(form).forEach(([k,v]) => { 
      if(v) {
        data.append(k,v);
        console.log(`Appended form field '${k}':`, v instanceof File ? `File [${v.name}, ${v.size} bytes]` : v);
      }
    });
    data.append('page', 1);
    data.append('limit', 20);
    
    try {
      console.log("Sending multipart request to '/api/match'...");
      const res = await fetch('/api/match', { 
        method: 'POST', 
        body: data,
        signal: signal
      });
      clearTimeout(timeoutId);
      console.log(`Received network response. Status: ${res.status} (${res.statusText})`);
      
      if (!res.ok) {
        const errText = await res.text();
        console.error("API response error body:", errText);
        let parsedErr;
        try {
          parsedErr = JSON.parse(errText);
        } catch(pErr) {}
        throw new Error(parsedErr?.detail || `Server returned error status ${res.status}`);
      }
      
      const result = await res.json();
      console.log("Parsed matching response successfully:", result);
      setJobs(result.matched_jobs || []);
      if (result.matched_jobs?.length === 0) {
        console.warn("No matched jobs found in API response.");
      }
    } catch(err) {
      if (err.name === 'AbortError') {
        console.error("Request aborted due to 30-second client-side timeout.");
        setError("Request Timed Out. The server took too long to respond. This is typically due to external API search delays. Please try again or check the server logs.");
      } else {
        console.error("Frontend Request Failure:", err);
        setError(err.message || "An unexpected error occurred while fetching matching jobs.");
      }
    } finally {
      setLoading(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      console.log("--- Frontend Submission Cycle Completed ---");
    }
  };

  return (
    <div className="dashboard-grid">
      <motion.section initial={{x: -20, opacity: 0}} animate={{x: 0, opacity: 1}} className="card">
        <h2 style={{marginBottom:'8px'}}>AI Profile Builder</h2>
        <p style={{color:'var(--text-secondary)', marginBottom:'24px', fontSize:'0.9rem'}}>Build your profile to discover roles aligned with your technical skills.</p>
        
        <form onSubmit={submit}>
          <div className="input-group">
            <label>Full Name</label>
            <input required value={form.name} onChange={update('name')} placeholder="Alex Mercer" />
          </div>
          <div className="input-group">
            <label>Email</label>
            <input required type="email" value={form.email} onChange={update('email')} placeholder="alex@university.edu" />
          </div>
          <div className="input-group">
            <label>Target Roles</label>
            <input value={form.desired_roles} onChange={update('desired_roles')} placeholder="Software Engineer, Backend Developer" />
          </div>
          <div className="input-group">
            <label>Core Skills</label>
            <textarea value={form.skills} onChange={update('skills')} placeholder="python, react, system design, aws" rows={2} />
          </div>
          <div className="input-group">
            <label>Resume Upload</label>
            <div 
              className={`drag-drop-zone ${dragActive?'active':''}`}
              onDragOver={(e)=>{e.preventDefault(); setDragActive(true);}}
              onDragLeave={()=>setDragActive(false)}
              onDrop={(e)=>{e.preventDefault(); setDragActive(false); if(e.dataTransfer.files[0]) setForm({...form, resume: e.dataTransfer.files[0]})}}
              onClick={() => fileRef.current.click()}
            >
              <input type="file" ref={fileRef} hidden onChange={update('resume')} accept=".pdf,.doc,.docx" />
              <Upload size={32} style={{marginBottom:'12px', color:'var(--accent-primary)'}} />
              {form.resume ? <p style={{color:'var(--color-success)'}}><CheckCircle size={16}/> {form.resume.name}</p> : <p>Drop resume here or click to browse</p>}
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Analyzing Profile...' : 'Discover Perfect Matches'}
          </button>
        </form>
      </motion.section>

      <section>
        {loading ? (
          <PipelineLoader elapsedTime={elapsedTime} />
        ) : error ? (
          <div className="card" style={{textAlign:'center', padding:'40px 20px', border:'1px solid rgba(239, 68, 68, 0.4)', background:'rgba(239, 68, 68, 0.05)'}}>
            <h3 style={{color:'var(--color-danger)', marginBottom:'12px'}}>Match Engine Error</h3>
            <p style={{color:'var(--text-secondary)', marginBottom:'20px'}}>{error}</p>
            <button onClick={() => setError(null)} className="btn-primary" style={{width:'auto', display:'inline-block'}}>Dismiss</button>
          </div>
        ) : jobs.length > 0 ? (
          <div className="jobs-list">
            {jobs.map(job => <JobCard key={job.id} job={job} />)}
          </div>
        ) : (
          <div className="card" style={{textAlign:'center', padding:'60px 20px'}}>
            <Briefcase size={48} style={{color:'var(--text-secondary)', marginBottom:'16px', opacity:0.5}} />
            <h3>Awaiting Profile</h3>
            <p style={{color:'var(--text-secondary)', marginTop:'8px'}}>Fill out your profile on the left to see strictly aligned, verified engineering jobs in India.</p>
          </div>
        )}
      </section>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="navbar">
          <Link to="/" className="brand">
            <Briefcase className="brand-logo" size={28} />
            <span className="brand-name">CareerAlign<span className="accent-text">.ai</span></span>
          </Link>
          <div className="nav-links">
            <Link to="/" className="nav-link">Find Jobs</Link>
            <Link to="/saved" className="nav-link">Saved</Link>
            <Link to="/login" className="nav-link" style={{display:'flex', alignItems:'center', gap:'6px'}}><User size={18}/> Login</Link>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/saved" element={<div className="card"><h2>Saved Jobs</h2><p>Login to view saved jobs.</p></div>} />
          <Route path="/login" element={<div className="card" style={{maxWidth:'400px', margin:'0 auto'}}><h2>Login</h2><p>Auth module coming soon.</p></div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
