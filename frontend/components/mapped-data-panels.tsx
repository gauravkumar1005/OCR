import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { titleCase } from "@/lib/format";

type MappedData = {
  summary?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  sections?: Array<Record<string, unknown>>;
  tables?: Array<Record<string, unknown>>;
} | null;

const groups: Array<{
  title: string;
  keys: string[];
}> = [
  { title: "Claim Information", keys: ["claimNumber", "documentType"] },
  { title: "Patient Information", keys: ["patientName", "patientAge", "gender"] },
  { title: "Policy Information", keys: ["policyNumber", "insuranceCompany", "tpaName"] },
  { title: "Hospital Information", keys: ["hospitalName", "admissionDate", "dischargeDate"] },
  { title: "Financial Information", keys: ["authorizedAmount"] },
  { title: "Metadata", keys: ["pageCount", "processedAt"] }
];

function valueFor(data: MappedData, key: string) {
  if (!data) return null;
  if (key === "pageCount" || key === "processedAt") {
    return data.metadata?.[key];
  }
  return data.summary?.[key] ?? null;
}

export function MappedDataPanels({ mappedData }: { mappedData: MappedData }) {
  if (!mappedData) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-slate-400">No mapped data available for this document yet.</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <Card key={group.title}>
          <CardHeader>
            <CardTitle>{group.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              {group.keys.map((key) => {
                const value = valueFor(mappedData, key);
                return (
                  <div key={key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{titleCase(key)}</p>
                    <p className="mt-2 break-words text-sm font-medium text-white">
                      {value === null || value === undefined || value === "" ? "Not available" : String(value)}
                    </p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
