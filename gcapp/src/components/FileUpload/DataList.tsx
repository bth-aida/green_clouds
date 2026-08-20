import { useQuery } from "@tanstack/react-query";
import "./FileUpload.css";
import DataRow from "./DataRow";
import AxiosApi from "../ApiCall";

export type FileStatus = "ok" | "warning" | "loading";

export interface FileItem {
  id: number;
  name: string;
  status: FileStatus;
  info: string;
}

const getFiles = async (): Promise<FileItem[]> => {
  const response = await AxiosApi.get("/files");
  return response.data;
};

interface Props {
  deleteAll: boolean;
}

const FileList = ({ deleteAll }: Props) => {
  const {
    data: items,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["getFiles"],
    queryFn: getFiles,
  });

  if (isLoading)
    return (
      <div>
        <p>Connecting to the server...</p>
        <div className="spinner-grow"></div>
      </div>
    );
  if (error) return <div>Error...</div>;

  return (
    <div>
      <ul className="list-group m-5">
        {items?.map((item) => (
          <DataRow item={item} key={item.id} deleteAll={deleteAll} />
        ))}
      </ul>
    </div>
  );
};

export default FileList;
