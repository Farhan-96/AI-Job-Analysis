import { JobDetail } from "@/components/JobDetail";

type Props = {
  params: Promise<{ id: string }>;
};

const JobDetailPage = async ({ params }: Props) => {
  const { id } = await params;
  const jobId = Number(id);
  if (Number.isNaN(jobId)) {
    return <p className="text-sm text-danger">Invalid job id</p>;
  }
  return <JobDetail jobId={jobId} />;
};

export default JobDetailPage;
