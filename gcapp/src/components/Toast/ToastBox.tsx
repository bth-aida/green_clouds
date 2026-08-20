interface Props {
  title: string;
  info: string;
  time: string;
  onClose: () => void;
}

// single toast card
const ToastBox = ({ title, info, time, onClose }: Props) => {
  return (
    <div className="toast show my-2" role="alert">
      <div className="toast-header">
        <i className="bi bi-info-circle mx-3 my-1"></i>
        <strong className="me-auto">{title}</strong>
        <small className="text-body-secondary">{time}</small>
        <button type="button" className="btn-close" onClick={onClose}></button>
      </div>
      <div className="toast-body">{info}</div>
    </div>
  );
};

export default ToastBox;
