import { type ConfSection } from "./ConfigTypes";
import "./Config.css";

interface Props {
  configSection: ConfSection;
  configValues: Record<string, any>;
  updateConfigValue: (id: string, value: any) => void;
}

const ConfigSection = ({
  configSection,
  configValues,
  updateConfigValue,
}: Props) => {
  return (
    <div className="card-body">
      {/* section title */}
      <label className="form-label d-block lead">{configSection.title}</label>

      {configSection.children.map((child) => {
        if (child.type === "checkbox") {
          // checkbox element
          return (
            <div className="form-check" key={child.id}>
              <input
                className="form-check-input checkbox"
                type="checkbox"
                id={`checkbox-${child.id}`}
                checked={configValues[child.id] ?? false}
                onChange={(e) => updateConfigValue(child.id, e.target.checked)}
              />
              <label
                className="form-check-label"
                htmlFor={`checkbox-${child.id}`}
              >
                {child.label}
              </label>
            </div>
          );
        } else if (child.type === "textbox") {
          // Textbox element
          return (
            <div className="form-floating mb-3" key={child.id}>
              <input
                type="text"
                className="form-control"
                value={configValues[child.id]}
                onChange={(e) => updateConfigValue(child.id, e.target.value)}
                placeholder=""
              />
              <label>{child.label}</label>
            </div>
          );
        }
      })}
    </div>
  );
};

export default ConfigSection;
