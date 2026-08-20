import { useQuery } from "@tanstack/react-query";
import AxiosApi, { EnterApiKey, ServerWait } from "../ApiCall";
import Page from "../Page";
import { useCallback, useEffect, useState } from "react";
import type { Config } from "./ConfigTypes";
import ConfigSection from "./ConfigSection";
import { throttle } from "lodash";

// get the config from api
const getConfig = async () => {
  const response = await AxiosApi.get<Config>("/get-config");
  return response.data;
};

// config page
const ConfigPage = () => {
  // config form structure
  const [config, setConfig] = useState<Config | null>(null);

  // config data
  const [configValues, setConfigValues] = useState<Record<string, any>>({});

  // sends the config to api for saving
  const sendConfig = useCallback(
    throttle(async (confValues: Record<string, any>) => {
      if (Object.keys(confValues).length > 0) {
        try {
          await AxiosApi.post("/set-config", confValues);
        } catch (err) {
          console.error("Error when saving config", err);
        }
      }
    }, 500),
    [],
  );

  // function for updating the config values
  const updateConfigValue = (id: string, value: any) => {
    setConfigValues((prev) => ({ ...prev, [id]: value }));
  };

  // send data when config values are updated
  useEffect(() => {
    sendConfig(configValues);
  }, [configValues]);

  // a query run on load to fetch config
  const {
    data: configData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["config_query"],
    queryFn: getConfig,
    staleTime: Infinity,
    gcTime: 100,
  });

  // update config when data is updated
  useEffect(() => {
    if (configData) {
      setConfig(configData);
      // get values from all config components
      if (configData !== null) {
        const confValues: Record<string, any> = {};
        configData.sections.forEach((section) => {
          section.children.forEach((child) => {
            if (child.type === "checkbox") {
              confValues[child.id] = child.checked;
            } else if (child.type === "textbox") {
              confValues[child.id] = child.text;
            }
          });
        });

        // set values to hashmap
        setConfigValues(confValues);
      }
    }
  }, [configData]);

  // if loading, or error, we wait
  if (isLoading || error) {
    return ServerWait();
  }

  // if config is null
  if (config === null) {
    return EnterApiKey();
  }

  return (
    <Page title="Configuration">
      <div id="configForm" className="container w-80 mx-auto">
        <section className="card p-3 shadow-sm">
          {/* form components */}
          {config.sections.map((section) => (
            <ConfigSection
              key={section.id}
              configSection={section}
              configValues={configValues}
              updateConfigValue={updateConfigValue}
            />
          ))}
        </section>
      </div>
    </Page>
  );
};

export default ConfigPage;
