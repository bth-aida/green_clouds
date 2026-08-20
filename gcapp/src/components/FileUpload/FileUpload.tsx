import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useRef, useState } from "react";
import "./FileUpload.css";
import AxiosApi from "../ApiCall";
import "../Buttons/Button.css";

interface Props {
  setDeleteAll: (remove: boolean) => void;
}

const FileUpload = ({ setDeleteAll }: Props) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgess] = useState(0);
  const [showBar, setShowBar] = useState(0);
  const queryClient = useQueryClient();

  // file uploading, progress bar
  const { mutate, isPending } = useMutation({
    mutationFn: async (fileList: File[]) => {
      const formData = new FormData();
      fileList.forEach((file) => formData.append("files", file));
      const { data } = await AxiosApi.post("/upload", formData, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1),
          );
          setUploadProgess(progress);
          setShowBar(1);
        },
      });
      return data;
    },
    onSuccess: () => {
      // hide bar after 1 second
      setTimeout(() => setShowBar(0), 500);

      // get updated data
      setTimeout(
        () => queryClient.invalidateQueries({ queryKey: ["getFiles"] }),
        500,
      );

      // reset bar
      setTimeout(() => setUploadProgess(0), 1500);
    },
    onError: () => {
      console.log("File Upload Failed");
    },
  });

  // upload files click
  const uploadBtnClick = () => {
    fileInputRef.current?.click();
  };

  // delete all file items
  const { mutate: deleteAllFiles } = useMutation({
    mutationFn: () => AxiosApi.delete(`/files/all`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["getFiles"] }),
  });

  // handle files entered by user
  const handleFileUploadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDeleteAll(false);
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      mutate(files);
    }
  };

  return (
    <div>
      {/* invisible input */}
      <input
        type="file"
        multiple
        name="filename"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileUploadChange}
      />

      <div className="d-flex flex justify-content-center mt-3">
        {/* upload files button */}
        <button
          className="btn btn-dark-1 align-items-center gap-2 me-2"
          onClick={uploadBtnClick}
        >
          <i className="bi bi-plus-lg me-2"></i>
          Upload file(s)
        </button>

        <button
          className="btn btn-dark-1 align-items-center gap-2"
          onClick={() => {
            setDeleteAll(true);
            deleteAllFiles();
          }}
        >
          <i className="bi bi-trash me-2 text-danger"></i>
          Delete all files
        </button>
      </div>

      {/* progress bar */}
      <div className="mt-3 d-flex justify-content-center ">
        <div
          className={`progress mt-2 pbar ${isPending || showBar ? "pshow" : ""}`}
          role="progressbar"
          aria-label="Upload progress bar"
          aria-valuenow={uploadProgress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="progress-bar progress-bar-striped progress-bar-animated bg-dark"
            style={{ width: `${uploadProgress}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
