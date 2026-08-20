import axios from "axios";

export const AxiosApi = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
});

export const ServerWait = () => {
  return (
    <div>
      <p>Waiting on server...</p>
      <div className="spinner-grow"></div>
    </div>
  );
};

export const EnterApiKey = () => {
  return (
    <div>
      <p>Enter a valid API-key...</p>
    </div>
  );
};

export default AxiosApi;
