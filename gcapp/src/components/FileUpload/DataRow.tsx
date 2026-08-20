import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { FileItem, FileStatus } from "./DataList";
import AxiosApi from "../ApiCall";
import { useEffect } from "react";
import { Popover } from "bootstrap";

interface Props {
  item: FileItem;
  deleteAll: boolean;
}

// file status icon and popover
const getStatusIcon = (status: FileStatus, info: string): React.ReactNode => {
  const icons = {
    loading: (
      <div className="spinner-border spinner-border-sm ms-2" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
    ),
    ok: (
      <i
        className="bi bi-check-circle-fill ms-2"
        style={{ color: "#379928" }}
      ></i>
    ),
    warning: (
      <i
        className="bi bi-exclamation-triangle ms-2"
        style={{ color: "red" }}
      ></i>
    ),
  };

  return (
    <span
      className="d-inline-block"
      data-bs-toggle="popover"
      data-bs-trigger="hover focus"
      data-bs-content={info}
    >
      {icons[status]}
    </span>
  );
};

const DataRow = ({ item, deleteAll }: Props) => {
  const queryClient = useQueryClient();

  // delete item from list
  const {
    mutate: deleteItem,
    isPending,
    isSuccess,
  } = useMutation({
    mutationFn: (id: number) => AxiosApi.delete(`/files/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["getFiles"] }),
  });

  // popovers
  useEffect(() => {
    const popoverTriggerList = document.querySelectorAll(
      '[data-bs-toggle="popover"]',
    );
    const popovers = Array.from(popoverTriggerList).map(
      (el) => new Popover(el),
    );

    return () => popovers.forEach((p) => p.dispose());
  }, []);

  return (
    <li
      // Li box
      className={`d-flex list-group-item justify-content-between align-items-center data-row-li ${isPending || isSuccess || deleteAll ? "is-removing" : ""}`}
      key={item.id}
    >
      <div className="d-flex align-items-center">
        {/* file entry */}
        <span>{item.name}</span>

        {isPending || isSuccess || deleteAll
          ? getStatusIcon("loading", "")
          : getStatusIcon(item.status, item.info)}
      </div>
      {/* trash icon */}
      <button
        className="btn btn-link text-danger p-0 shadow-none delete-btn"
        onClick={() => deleteItem(item.id)}
        disabled={isPending || isSuccess}
      >
        <i className="bi bi-trash"></i>
      </button>
    </li>
  );
};

export default DataRow;
