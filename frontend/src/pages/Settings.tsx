import { useEffect, useState } from "react";
import { api, SystemInfo } from "../api";
import { Loading } from "../components/ui";
import { useAuth } from "../auth";

export default function Settings() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    api<SystemInfo>("/system/info").then(setInfo).catch(() => {});
  }, []);

  if (!info) return <Loading />;

  return (
    <div>
      <div className="card">
        <h2>⚙️ Settings &amp; System</h2>
        <table>
          <tbody>
            <tr>
              <td>Application</td>
              <td className="mono">{info.app}</td>
            </tr>
            <tr>
              <td>Version</td>
              <td className="mono">{info.version}</td>
            </tr>
            <tr>
              <td>Python</td>
              <td className="mono">{info.python}</td>
            </tr>
            <tr>
              <td>Demo mode</td>
              <td>{info.demo_mode ? "ON. Demonstration dataset loaded and clearly labelled" : "OFF"}</td>
            </tr>
            <tr>
              <td>Signed in as</td>
              <td>
                {user?.username} (<span className="chip neutral">{user?.role}</span>)
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Scientific governance</h3>
        <ul className="muted">
          <li>No synthetic value is ever presented as real Ghanaian surveillance data.</li>
          <li>Predictions are associations from models. They are not causal effects and not diagnoses.</li>
          <li>Resistance interpretation requires researcher-supplied validated definitions.</li>
          <li>Genetic marker ≠ phenotypic drug resistance.</li>
          <li>Audit logs record logins, dataset operations, training runs and report generation.</li>
          <li>Uploaded files are stored server-side; personally identifiable information must not be uploaded.</li>
        </ul>
      </div>

      <div className="card">
        <h3>Disclaimer</h3>
        <p className="muted">{info.disclaimer}</p>
      </div>
    </div>
  );
}
