import { useEffect, useState } from "react";
import ToastBox from "./ToastBox";

interface ToastMessage {
  id: number;
  title: string;
  info: string;
  time: string;
  duration: string;
}

interface Props {
  apiKey: string;
}

// manager for toasts
const ToastManager = ({ apiKey }: Props) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // websocket connection
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onmessage = (event) => {
      const newToast: ToastMessage = JSON.parse(event.data);
      setToasts((toasts) => [...toasts, newToast]);

      if (newToast.duration == "short") {
        setTimeout(() => {
          setToasts((toasts) => toasts.filter((t) => t.id !== newToast.id));
        }, 5000);
      }
    };

    return () => {
      socket.close();
    };
  }, [apiKey]);

  const dismissToast = (id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <div className="toast-container top-0 end-0 p-3">
      {toasts.map((t) => (
        <ToastBox
          key={t.id}
          title={t.title}
          info={t.info}
          time={t.time}
          onClose={() => dismissToast(t.id)}
        />
      ))}
    </div>
  );
};

export default ToastManager;
