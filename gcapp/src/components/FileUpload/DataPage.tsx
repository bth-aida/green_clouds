import { useQuery } from "@tanstack/react-query";
import AxiosApi, { EnterApiKey, ServerWait } from "../ApiCall";
import Page from "../Page";
import FileUpload from "./FileUpload";
import DataRow from "./DataRow";
import { useState } from "react";
import { HttpStatusCode } from "axios";

// file status
export type FileStatus = "ok" | "warning" | "loading";

/**
 * object representing a file
 */
export interface FileItem {
  id: number;
  name: string;
  status: FileStatus;
  info: string;
}

/**
 * get uploaded files from api
 */
const getFiles = async (): Promise<FileItem[]> => {
  const response = await AxiosApi.get("/files");
  return response.data;
};

const DataPage = () => {
  const [deleteAll, setDeleteAll] = useState(false);

  // when loading page, load files
  const {
    data: items,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["getFiles"],
    queryFn: getFiles,
  });

  if (isLoading || error) {
    return ServerWait();
  }

  if (items === null) {
    return EnterApiKey();
  }

  return (
    <Page title="Data">
      <div id="configForm" className="container w-80 mx-auto">
        <section className="card p-3 shadow-sm text-center">
          <div className="card-body">
            {/* title */}
            <label className="form-label d-block lead">File Upload</label>

            {/* file list */}
            <ul className="list-group m-5">
              {items?.map((item) => (
                <DataRow item={item} key={item.id} deleteAll={deleteAll} />
              ))}
            </ul>

            {/* file upload */}
            <FileUpload setDeleteAll={setDeleteAll} />
          </div>
        </section>
      </div>
    </Page>
  );
};

export default DataPage;
