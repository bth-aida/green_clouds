import { useState } from "react";
import "./ApiKeyEntry.css";
import AxiosApi from "../ApiCall";
import { useQuery } from "@tanstack/react-query";

// used for validating api key
export interface apiKeyResponse {
  status: string;
  api_key: string;
}

// api key status
const apiInputStatus: Record<string, string> = {
  valid: "is-valid",
  invalid: "is-invalid",
  idle: "",
};

interface Props {
  setApiKey: (key: string) => void;
}

const ApiKeyEntry = ({ setApiKey }: Props) => {
  // tempApiKey stores value in the text field
  const [tempApiKey, setTempApiKey] = useState("");

  // apiKeyStatus can be valid, invalid or idle
  const [apiKeyStatus, setApiKeyStatus] = useState("idle");

  // verifies the cookie api key by server call
  const verifySavedApiKey = async () => {
    const response = await AxiosApi.get<apiKeyResponse>(
      "/verify-saved-api-key",
    );
    if (response.data.api_key) {
      setTempApiKey(response.data.api_key);
      setApiKeyStatus("valid");
      setApiKey(response.data.api_key);
    }
    return response;
  };

  // query that is run on load, that verifies api key cookie
  const {} = useQuery({
    queryKey: ["apiVerifyKey"],
    queryFn: verifySavedApiKey,
    staleTime: Infinity,
    gcTime: 100,
  });

  // enter btn clicked
  const enterApiKeyClick = async () => {
    const response = await AxiosApi.post("/verify-new-api-key", {
      key: tempApiKey,
    });
    if (response.data.api_key) {
      setApiKeyStatus("valid");
      setApiKey(response.data.api_key);
    } else {
      setApiKeyStatus("invalid");
    }
  };

  const generateApiKeyClick = async () => {
    const response = await AxiosApi.post<apiKeyResponse>("/generate-api-key");
    if (response.data.api_key) {
      setTempApiKey(response.data.api_key);
      setApiKey(response.data.api_key);
    }
    setApiKeyStatus("valid");
  };

  const apiKeyInputChange = (apiKey: string) => {
    setTempApiKey(apiKey);
    setApiKeyStatus("idle");
  };

  return (
    <div className="m-5">
      <div className="input-group" style={{ width: "auto" }}>
        <div className="form-floating flex-grow-1">
          <input
            type="text"
            className={`form-control  ${apiInputStatus[apiKeyStatus] || ""}`}
            id="apiKeyInput"
            placeholder=""
            value={tempApiKey}
            onChange={(e) => apiKeyInputChange(e.target.value)}
          />
          <label htmlFor="apiKeyInput">API Key</label>
        </div>
      </div>
      <p
        className={`mx-2 ${apiKeyStatus === "invalid" ? "" : "invisible"}`}
        style={{ color: "#d82d41", fontSize: "small" }}
      >
        Invalid API key
      </p>
      <button
        className="btn px-5 py-2 btn-dark-1 me-3 mt-3"
        type="button"
        onClick={enterApiKeyClick}
      >
        <i
          className="bi bi-filetype-key me-2"
          style={{ color: "var(--green-primary)" }}
        ></i>
        Enter API key
      </button>
      <button
        className="btn px-5 py-2 btn-dark-1 mt-3"
        type="button"
        onClick={generateApiKeyClick}
      >
        <i
          className="bi bi-key me-2"
          style={{ color: "var(--blue-primary)" }}
        ></i>
        Generate new API key
      </button>
    </div>
  );
};

export default ApiKeyEntry;
