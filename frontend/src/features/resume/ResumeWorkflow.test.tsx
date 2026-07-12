import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResumeWorkflow } from "@/features/resume/ResumeWorkflow";

describe("ResumeWorkflow", () => {
  it("asks the user to sign in when no access token is available", () => {
    render(<ResumeWorkflow accessToken={null} />);

    expect(screen.getByText(/Sign in to create a profile and upload a resume/i)).toBeInTheDocument();
  });

  it("shows profile fields when signed in", () => {
    render(<ResumeWorkflow accessToken="token" />);

    expect(screen.getByLabelText(/Career goal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Preferred role/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Create profile/i })).toBeInTheDocument();
  });
});
