import { z } from "zod";

export const profileSchema = z.object({
  career_goal: z.string().min(1, "Career goal is required.").max(120),
  preferred_role: z.string().min(1, "Preferred role is required.").max(120),
});

export const jobDescriptionSchema = z.object({
  text: z.string().min(100, "Paste at least 100 characters from the job description.").max(60000),
});

export const githubSchema = z.object({
  username_or_url: z.string().min(1, "GitHub username or URL is required.").max(120),
});

export const portfolioSchema = z.object({
  url: z.string().min(1, "Portfolio URL is required.").max(500),
});

export const linkedInSchema = z.object({
  text: z.string().min(50, "Paste at least 50 characters from LinkedIn.").max(60000),
});

export type ProfileValues = z.infer<typeof profileSchema>;
export type JobDescriptionValues = z.infer<typeof jobDescriptionSchema>;
export type GitHubValues = z.infer<typeof githubSchema>;
export type PortfolioValues = z.infer<typeof portfolioSchema>;
export type LinkedInValues = z.infer<typeof linkedInSchema>;
