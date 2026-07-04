import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { formatDate, titleCase } from "@/lib/format";

type Primitive = string | number | boolean | null | undefined;

type MappedData = {
  summary?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  sections?: Array<Record<string, unknown>>;
  tables?: Array<Record<string, unknown>>;
} | null;

type FieldDefinition = {
  label: string;
  paths: string[][];
};

type SectionDefinition = {
  title: string;
  fields: FieldDefinition[];
};

const SECTION_DEFINITIONS: SectionDefinition[] = [
  {
    title: "Claim Information",
    fields: [
      { label: "Claim ID", paths: [["summary", "claimId"], ["summary", "claim_id"], ["claimId"], ["claim_id"]] },
      { label: "Claim Number", paths: [["summary", "claimNumber"], ["summary", "claim_number"], ["claimNumber"], ["claim_number"]] },
      { label: "Document Type", paths: [["summary", "documentType"], ["summary", "document_type"], ["documentType"], ["document_type"]] }
    ]
  },
  {
    title: "Patient Information",
    fields: [
      { label: "Patient Name", paths: [["summary", "patientName"], ["summary", "patient_name"], ["patientName"], ["patient_name"]] },
      { label: "Patient Age", paths: [["summary", "patientAge"], ["summary", "patient_age"], ["patientAge"], ["patient_age"]] },
      { label: "Gender", paths: [["summary", "gender"], ["gender"]] },
      { label: "Date of Birth", paths: [["summary", "dateOfBirth"], ["summary", "dob"], ["dateOfBirth"], ["dob"]] }
    ]
  },
  {
    title: "Policy Information",
    fields: [
      { label: "Policy Number", paths: [["summary", "policyNumber"], ["summary", "policy_number"], ["policyNumber"], ["policy_number"]] },
      { label: "Insurance Company", paths: [["summary", "insuranceCompany"], ["summary", "insurance_company"], ["insuranceCompany"], ["insurance_company"]] },
      { label: "TPA Name", paths: [["summary", "tpaName"], ["summary", "tpa_name"], ["tpaName"], ["tpa_name"]] },
      { label: "Policy Holder", paths: [["summary", "policyHolderName"], ["summary", "policy_holder_name"], ["policyHolderName"], ["policy_holder_name"]] }
    ]
  },
  {
    title: "Hospital Information",
    fields: [
      { label: "Hospital Name", paths: [["summary", "hospitalName"], ["summary", "hospital_name"], ["hospitalName"], ["hospital_name"]] },
      { label: "Admission Date", paths: [["summary", "admissionDate"], ["summary", "admission_date"], ["admissionDate"], ["admission_date"]] },
      { label: "Discharge Date", paths: [["summary", "dischargeDate"], ["summary", "discharge_date"], ["dischargeDate"], ["discharge_date"]] },
      { label: "Department", paths: [["summary", "department"], ["department"]] }
    ]
  },
  {
    title: "Diagnosis",
    fields: [
      { label: "Primary Diagnosis", paths: [["summary", "diagnosis"], ["summary", "primaryDiagnosis"], ["diagnosis"], ["primaryDiagnosis"]] },
      { label: "Provisional Diagnosis", paths: [["summary", "provisionalDiagnosis"], ["summary", "provisional_diagnosis"], ["provisionalDiagnosis"], ["provisional_diagnosis"]] },
      { label: "Final Diagnosis", paths: [["summary", "finalDiagnosis"], ["summary", "final_diagnosis"], ["finalDiagnosis"], ["final_diagnosis"]] },
      { label: "Procedure", paths: [["summary", "procedure"], ["summary", "procedureName"], ["procedure"], ["procedureName"]] }
    ]
  },
  {
    title: "Financial Information",
    fields: [
      { label: "Claimed Amount", paths: [["summary", "claimedAmount"], ["summary", "claimed_amount"], ["claimedAmount"], ["claimed_amount"]] },
      { label: "Authorized Amount", paths: [["summary", "authorizedAmount"], ["summary", "authorized_amount"], ["authorizedAmount"], ["authorized_amount"]] },
      { label: "Bill Amount", paths: [["summary", "billAmount"], ["summary", "bill_amount"], ["billAmount"], ["bill_amount"]] },
      { label: "Payable Amount", paths: [["summary", "payableAmount"], ["summary", "payable_amount"], ["payableAmount"], ["payable_amount"]] }
    ]
  },
  {
    title: "Doctor Information",
    fields: [
      { label: "Doctor Name", paths: [["summary", "doctorName"], ["summary", "treatingDoctor"], ["doctorName"], ["treatingDoctor"]] },
      { label: "Speciality", paths: [["summary", "speciality"], ["summary", "doctorSpeciality"], ["speciality"], ["doctorSpeciality"]] },
      { label: "Physician", paths: [["summary", "physicianName"], ["summary", "physician_name"], ["physicianName"], ["physician_name"]] }
    ]
  },
  {
    title: "Metadata",
    fields: [
      { label: "Page Count", paths: [["metadata", "pageCount"], ["metadata", "page_count"], ["summary", "pageCount"], ["pageCount"]] },
      { label: "Processed At", paths: [["metadata", "processedAt"], ["metadata", "processed_at"], ["summary", "processedAt"], ["processedAt"]] },
      { label: "Created At", paths: [["metadata", "createdAt"], ["createdAt"]] },
      { label: "Updated At", paths: [["metadata", "updatedAt"], ["updatedAt"]] }
    ]
  }
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getValueAtPath(source: Record<string, unknown> | null, path: string[]): unknown {
  if (!source) return undefined;

  let current: unknown = source;
  for (const key of path) {
    if (!isRecord(current)) return undefined;
    current = current[key];
    if (current === undefined || current === null) {
      return current;
    }
  }

  return current;
}

function firstAvailableValue(source: Record<string, unknown> | null, paths: string[][]): unknown {
  for (const path of paths) {
    const value = getValueAtPath(source, path);
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }
  return null;
}

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;

  if (value instanceof Date) {
    return formatDate(value.toISOString());
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    if (value.every((item) => item === null || item === undefined || ["string", "number", "boolean"].includes(typeof item))) {
      return value.map((item) => String(item)).join(", ");
    }
    return JSON.stringify(value, null, 2);
  }

  if (isRecord(value)) {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function hasRenderableValue(value: unknown): boolean {
  const formatted = formatValue(value);
  return Boolean(formatted && formatted.trim().length > 0);
}

function hasMappedContent(data: MappedData): boolean {
  if (!data) return false;
  if (data.summary && Object.keys(data.summary).length > 0) return true;
  if (data.metadata && Object.keys(data.metadata).length > 0) return true;
  if (data.sections?.some((section) => Object.keys(section).length > 0)) return true;
  if (data.tables?.some((table) => Object.keys(table).length > 0)) return true;
  return false;
}

function FieldCard({ label, value }: { label: string; value: unknown }) {
  const formatted = formatValue(value);
  if (!formatted) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 shadow-sm shadow-black/20">
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <div className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-100">
        {formatted}
      </div>
    </div>
  );
}

function SectionCard({ title, fields, source }: { title: string; fields: FieldDefinition[]; source: Record<string, unknown> | null }) {
  const resolvedFields = fields
    .map((field) => ({ label: field.label, value: firstAvailableValue(source, field.paths) }))
    .filter((field) => hasRenderableValue(field.value));

  if (resolvedFields.length === 0) return null;

  return (
    <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg text-white">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {resolvedFields.map((field) => (
            <FieldCard key={`${title}-${field.label}`} label={field.label} value={field.value} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function JsonCard({ title, value }: { title: string; value: unknown }) {
  if (value === null || value === undefined) return null;

  const formatted = formatValue(value);
  if (!formatted) return null;

  return (
    <Card className="border-cyan-400/15 bg-slate-950/60 shadow-lg shadow-black/10">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg text-white">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-xs leading-6 text-slate-200">
          {formatted}
        </pre>
      </CardContent>
    </Card>
  );
}

export function MappedDataPanels({ mappedData, rawOcr }: { mappedData: MappedData; rawOcr: Record<string, unknown> | null }) {
  if (hasMappedContent(mappedData)) {
    const source = mappedData?.summary ?? null;
    const metadataSource = mappedData?.metadata ?? null;

    return (
      <div className="space-y-6">
        {SECTION_DEFINITIONS.slice(0, 6).map((section) => (
          <SectionCard key={section.title} title={section.title} fields={section.fields} source={source} />
        ))}

        <SectionCard title="Metadata" fields={SECTION_DEFINITIONS[6].fields} source={metadataSource ?? source} />

        {Array.isArray(mappedData?.sections) && mappedData.sections.length > 0 ? (
          <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-white">Additional Sections</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mappedData.sections.map((section, index) => {
                const sectionTitle =
                  (typeof section.title === "string" && section.title.trim()) ||
                  (typeof section.name === "string" && section.name.trim()) ||
                  `Section ${index + 1}`;
                const entries = Object.entries(section).filter(([key, value]) => key !== "title" && key !== "name" && hasRenderableValue(value));
                if (entries.length === 0) return null;

                return (
                  <div key={`${sectionTitle}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">{sectionTitle}</p>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      {entries.map(([key, value]) => (
                        <FieldCard key={key} label={titleCase(key)} value={value} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        ) : null}

        {Array.isArray(mappedData?.tables) && mappedData.tables.length > 0 ? (
          <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-white">Tables</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mappedData.tables.map((table, index) => (
                <div key={`table-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Table {index + 1}</p>
                  <pre className="mt-3 max-h-[360px] overflow-auto whitespace-pre-wrap break-words rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-xs leading-6 text-slate-200">
                    {JSON.stringify(table, null, 2)}
                  </pre>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : null}

        <JsonCard title="Mapped JSON" value={mappedData} />
      </div>
    );
  }

  if (rawOcr) {
    return (
      <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-white">Raw OCR JSON</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="max-h-[760px] overflow-auto rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-xs leading-6 text-slate-200">
            {JSON.stringify(rawOcr, null, 2)}
          </pre>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
      <CardContent className="p-6 text-sm text-slate-400">No mapped data or raw OCR data is available for this document yet.</CardContent>
    </Card>
  );
}
