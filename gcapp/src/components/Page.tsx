interface Props {
  title: string;
  children: React.ReactNode;
}

const Page = ({ title, children }: Props) => {
  return (
    <div>
      <h1 className="display-6 mb-4">{title}</h1>
      <div>{children}</div>
    </div>
  );
};

export default Page;
