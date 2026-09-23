export type NavItem = {
  href: string;
  label: string;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/jobs", label: "Jobs" },
  { href: "/jobs/import", label: "Job Import" },
  { href: "/applications", label: "Applications" },
  { href: "/resumes", label: "Resumes" },
  { href: "/approval", label: "Approval Queue" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Settings" },
];
