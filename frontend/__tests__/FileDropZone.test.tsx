import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { useState } from "react";
import { FileDropZone } from "@/app/evaluate-contract/FileDropZone";

function ControlledDropZone({
  onFileChangeSpy,
}: {
  onFileChangeSpy?: ReturnType<typeof vi.fn>;
}) {
  const [file, setFile] = useState<File | null>(null);
  return (
    <FileDropZone
      file={file}
      onFileChange={(f) => {
        setFile(f);
        onFileChangeSpy?.(f);
      }}
    />
  );
}

describe("FileDropZone", () => {
  it("renders the drop zone with drag and drop prompt", () => {
    render(<FileDropZone file={null} onFileChange={vi.fn()} />);
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
  });

  it("renders a browse button", () => {
    render(<FileDropZone file={null} onFileChange={vi.fn()} />);
    expect(screen.getByText(/browse/i)).toBeInTheDocument();
  });

  it("has a hidden file input with correct accept types", () => {
    render(<FileDropZone file={null} onFileChange={vi.fn()} />);
    const input =
      screen.getByLabelText<HTMLInputElement>(/upload contract file/i);
    expect(input).toBeInTheDocument();
    expect(input.accept).toBe(".txt,.pdf,.doc,.docx");
  });

  it("renders staged file when file prop is provided", () => {
    const file = new File(["content"], "contract.txt", { type: "text/plain" });
    render(<FileDropZone file={file} onFileChange={vi.fn()} />);

    expect(screen.getByText("contract.txt")).toBeInTheDocument();
  });

  it("stages a valid file and calls onFileChange", async () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const file = new File(["content"], "contract.txt", { type: "text/plain" });
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file,
    );

    expect(spy).toHaveBeenCalledWith(file);
    expect(screen.getByText("contract.txt")).toBeInTheDocument();
  });

  it("shows error for invalid file extension", () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const file = new File(["content"], "image.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText(/upload contract file/i), {
      target: { files: [file] },
    });

    expect(screen.getByText(/file type not allowed/i)).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("shows error for oversized file", () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const bigContent = new ArrayBuffer(11 * 1024 * 1024);
    const file = new File([bigContent], "big.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText(/upload contract file/i), {
      target: { files: [file] },
    });

    expect(screen.getByText(/10 MB/i)).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("removes staged file when remove button is clicked", async () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const file = new File(["content"], "contract.txt", { type: "text/plain" });
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file,
    );
    expect(screen.getByText("contract.txt")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /remove/i }));
    expect(screen.queryByText("contract.txt")).not.toBeInTheDocument();
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
    expect(spy).toHaveBeenLastCalledWith(null);
  });

  it("replaces staged file when a new file is selected", async () => {
    render(<ControlledDropZone />);

    const file1 = new File(["a"], "first.txt", { type: "text/plain" });
    const file2 = new File(["b"], "second.txt", { type: "text/plain" });

    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file1,
    );
    expect(screen.getByText("first.txt")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /remove/i }));
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file2,
    );

    expect(screen.queryByText("first.txt")).not.toBeInTheDocument();
    expect(screen.getByText("second.txt")).toBeInTheDocument();
  });

  it("accepts a valid file via drag and drop", () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const dropZone = screen.getByText(/drag.+drop/i).closest("div")!;
    const file = new File(["content"], "contract.txt", { type: "text/plain" });

    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

    expect(spy).toHaveBeenCalledWith(file);
    expect(screen.getByText("contract.txt")).toBeInTheDocument();
  });

  it("rejects an invalid file via drag and drop", () => {
    const spy = vi.fn();
    render(<ControlledDropZone onFileChangeSpy={spy} />);

    const dropZone = screen.getByText(/drag.+drop/i).closest("div")!;
    const file = new File(["content"], "image.jpg", { type: "image/jpeg" });

    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

    expect(screen.getByText(/file type not allowed/i)).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });
});
