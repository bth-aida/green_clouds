import { useQuery } from "@tanstack/react-query";
import AxiosApi from "./ApiCall";
import type { apiKeyResponse } from "./Home/ApiKeyEntry";

// ApiKey update
interface CookieProps {
  setApiKey: (key: string) => void;
}

const ApiKeyFetch = ({ setApiKey }: CookieProps) => {
  // verifies the cookie api key by server call
  const verifyCookieApiKey = async () => {
    const response = await AxiosApi.get<apiKeyResponse>(
      "/verify-saved-api-key",
    );
    if (response.data.api_key) {
      setApiKey(response.data.api_key);
    }
    return response;
  };

  // query that is run on load, that verifies api key cookie
  const {} = useQuery({
    queryKey: ["verifyKey"],
    queryFn: verifyCookieApiKey,
    staleTime: Infinity,
    gcTime: 100,
  });
  return null;
};

export default ApiKeyFetch;
