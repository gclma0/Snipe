import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import {
  GitHubValues,
  JobDescriptionValues,
  LinkedInValues,
  PortfolioValues,
  ProfileValues,
  githubSchema,
  jobDescriptionSchema,
  linkedInSchema,
  portfolioSchema,
  profileSchema,
} from "@/features/resume/resumeWorkflowForms";

export function useResumeWorkflowForms() {
  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      career_goal: "Prepare for a target role",
      preferred_role: "",
    },
  });
  const jobForm = useForm<JobDescriptionValues>({
    resolver: zodResolver(jobDescriptionSchema),
    defaultValues: {
      text: "",
    },
  });
  const githubForm = useForm<GitHubValues>({
    resolver: zodResolver(githubSchema),
    defaultValues: {
      username_or_url: "",
    },
  });
  const portfolioForm = useForm<PortfolioValues>({
    resolver: zodResolver(portfolioSchema),
    defaultValues: {
      url: "",
    },
  });
  const linkedInForm = useForm<LinkedInValues>({
    resolver: zodResolver(linkedInSchema),
    defaultValues: {
      text: "",
    },
  });

  return {
    profileForm,
    jobForm,
    githubForm,
    portfolioForm,
    linkedInForm,
  };
}
