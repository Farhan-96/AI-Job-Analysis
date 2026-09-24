import { SearchProfileEditor } from "@/components/SearchProfileEditor";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function EditSearchProfilePage({ params }: Props) {
  const { id } = await params;
  return <SearchProfileEditor profileId={Number(id)} />;
}
