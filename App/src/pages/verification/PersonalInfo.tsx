import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { RadioGroup } from "@/components/verification/RadioGroup";
import { SearchableList } from "@/components/verification/SearchableList";
import { ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";

const getJobCategories = (t: (key: string) => string) => [
  { id: "chief-exec", label: t('verify.personal.jobs.chiefExec') },
  { id: "general-managers", label: t('verify.personal.jobs.generalManagers') },
  { id: "advertising", label: t('verify.personal.jobs.advertising') },
  { id: "marketing", label: t('verify.personal.jobs.marketing') },
  { id: "sales", label: t('verify.personal.jobs.sales') },
  { id: "admin-services", label: t('verify.personal.jobs.adminServices') },
  { id: "computer-info", label: t('verify.personal.jobs.computerInfo') },
  { id: "financial", label: t('verify.personal.jobs.financial') },
  { id: "hr", label: t('verify.personal.jobs.hr') },
  { id: "training", label: t('verify.personal.jobs.training') },
  { id: "software-dev", label: t('verify.personal.jobs.softwareDev') },
  { id: "software-sys", label: t('verify.personal.jobs.softwareSys') },
  { id: "web-dev", label: t('verify.personal.jobs.webDev') },
  { id: "database-admin", label: t('verify.personal.jobs.databaseAdmin') },
  { id: "security-analyst", label: t('verify.personal.jobs.securityAnalyst') },
  { id: "student", label: t('verify.personal.jobs.student') },
  { id: "unemployed", label: t('verify.personal.jobs.unemployed') },
  { id: "retired", label: t('verify.personal.jobs.retired') },
  { id: "other", label: t('verify.personal.jobs.other') },
];

const getSalaryRanges = (t: (key: string) => string) => [
  { id: "less-75k", label: t('verify.personal.salary.less75k') },
  { id: "75k-185k", label: t('verify.personal.salary.75kTo185k') },
  { id: "185k-370k", label: t('verify.personal.salary.185kTo370k') },
  { id: "370k-735k", label: t('verify.personal.salary.370kTo735k') },
  { id: "more-735k", label: t('verify.personal.salary.more735k') },
];

const getAccountPurposes = (t: (key: string) => string) => [
  { id: "personal", label: t('verify.personal.purpose.personal') },
  { id: "investment", label: t('verify.personal.purpose.investment') },
  { id: "savings", label: t('verify.personal.purpose.savings') },
];

const MAX_OTHER_LENGTH = 100;

const PersonalInfo = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [showJobCategories, setShowJobCategories] = useState(false);
  const [occupation, setOccupation] = useState<string | null>(null);
  const [salary, setSalary] = useState<string | null>(null);
  const [purpose, setPurpose] = useState<string | null>(null);
  const [otherPurpose, setOtherPurpose] = useState("");

  const jobCategories = getJobCategories(t);
  const selectedJob = jobCategories.find((j) => j.id === occupation);
  const isValid = occupation && salary && (purpose || otherPurpose.trim().length > 0);

  if (showJobCategories) {
    return (
      <SearchableList
        title={t('verify.personal.jobCategory')}
        items={jobCategories}
        value={occupation}
        onChange={setOccupation}
        onClose={() => setShowJobCategories(false)}
        searchPlaceholder={t('verify.personal.search')}
      />
    );
  }

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify/steps")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={1} totalSteps={4} />
        </div>

        <div className="flex-1 px-6 py-4 overflow-y-auto pb-28">
          <h1 className="text-2xl font-bold mb-6">
            {t('verify.personal.title')}
          </h1>

          {/* Occupation */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.personal.occupation')} <span className="text-destructive">*</span>
            </label>
            <button
              onClick={() => setShowJobCategories(true)}
              className="w-full flex items-center justify-between p-4 rounded-xl border border-border hover:border-muted-foreground transition-colors"
            >
              <span className={occupation ? "" : "text-muted-foreground"}>
                {selectedJob?.label || t('verify.personal.jobCategory')}
              </span>
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Annual Salary */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.personal.annualSalary')} <span className="text-destructive">*</span>
            </label>
            <RadioGroup
              options={getSalaryRanges(t)}
              value={salary}
              onChange={setSalary}
            />
          </div>

          {/* Account Purpose */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.personal.accountPurpose')} <span className="text-destructive">*</span>
            </label>
            <RadioGroup
              options={getAccountPurposes(t)}
              value={purpose}
              onChange={(val) => {
                setPurpose(val);
                setOtherPurpose("");
              }}
            />
            
            {/* Others input field */}
            <div className="mt-2">
              <label className="text-sm text-muted-foreground mb-2 block">
                {t('verify.personal.othersInput')}
              </label>
              <Input
                value={otherPurpose}
                onChange={(e) => {
                  const value = e.target.value.slice(0, MAX_OTHER_LENGTH);
                  setOtherPurpose(value);
                  if (value.trim().length > 0) {
                    setPurpose(null);
                  }
                }}
                placeholder={t('verify.personal.enterAnswer')}
                maxLength={MAX_OTHER_LENGTH}
                className="rounded-xl"
              />
              <div className="flex justify-end mt-1">
                <span className="text-xs text-muted-foreground">
                  {otherPurpose.length}/{MAX_OTHER_LENGTH}
                </span>
              </div>
            </div>
          </div>

          <PoweredByFooter />
        </div>

        {/* Button */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/monthly-volume")}
            disabled={!isValid}
            className={`karta-btn-primary ${
              !isValid ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {t('verify.personal.continue')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default PersonalInfo;
