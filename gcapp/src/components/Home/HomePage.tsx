import ApiKeyEntry from "./ApiKeyEntry";
import Page from "../Page";
import { useQuery } from "@tanstack/react-query";
import AxiosApi, { ServerWait } from "../ApiCall";

// look for connection to server
const getResponse = async () => {
  const response = await AxiosApi.get("/");
  return response;
};

interface Props {
  setApiKey: (key: string) => void;
}

const HomePage = ({ setApiKey }: Props) => {
  // look for server connection
  const { isLoading, error } = useQuery({
    queryKey: ["ping"],
    queryFn: getResponse,
    staleTime: 0,
    gcTime: 0,
  });

  if (isLoading || error) {
    return ServerWait();
  }

  return (
    <Page title="Home">
      <div id="configForm" className="container w-80 mx-auto">
        <section className="card p-3 shadow-sm text-center">
          <div className="card-body">
            <label className="form-label d-block lead">Api key entry</label>
            <ApiKeyEntry setApiKey={setApiKey} />
          </div>
        </section>
      </div>
    </Page>
  );
};

export default HomePage;
