import { motion } from "framer-motion";

interface Props {
  title: string;
  children: React.ReactNode;
}

const ResultCard = ({ children, title }: Props) => {
  return (
    <motion.section
      initial={{ opacity: 0, y: -15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{
        opacity: 0.5,
        y: -15,
        height: 0,
        marginBottom: 0,
        transition: { duration: 3 },
      }}
      transition={{ duration: 0.4 }}
      className="card p-3 mt-2 shadow-sm text-center"
    >
      <div className="card-body">
        {/* title */}
        <label className="form-label d-block lead">{title}</label>
        {/* content */}
        {children}
      </div>
    </motion.section>
  );
};

export default ResultCard;
