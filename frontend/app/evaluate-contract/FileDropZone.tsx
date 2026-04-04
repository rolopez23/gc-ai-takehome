'use client';

import { useRef, useState } from 'react';
import {
  ALLOWED_EXTENSIONS,
  validateFileExtension,
  validateFileSize,
} from './validation';

interface FileDropZoneProps {
  onFileChange: (file: File | null) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropZone({ onFileChange }: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  function processFile(file: File) {
    setError(null);

    if (!validateFileExtension(file.name)) {
      setError(
        `File type not allowed. Accepted formats: ${ALLOWED_EXTENSIONS.join(', ')}`,
      );
      return;
    }

    if (!validateFileSize(file.size)) {
      setError('File is too large. Maximum size is 5 MB.');
      return;
    }

    setStagedFile(file);
    onFileChange(file);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  }

  function handleRemove() {
    setStagedFile(null);
    onFileChange(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  function handleDragEnter(e: React.DragEvent) {
    e.preventDefault();
    dragCounter.current++;
    if (!isDragging) setIsDragging(true);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    dragCounter.current--;
    if (dragCounter.current === 0) setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    dragCounter.current = 0;
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }

  if (stagedFile) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-foreground/20 p-4">
        <div>
          <p className="font-medium">{stagedFile.name}</p>
          <p className="text-sm text-foreground/60">
            {formatFileSize(stagedFile.size)}
          </p>
        </div>
        <button
          type="button"
          onClick={handleRemove}
          className="rounded-md px-3 py-1 text-sm text-foreground/60 hover:bg-foreground/10"
        >
          Remove
        </button>
      </div>
    );
  }

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center ${
        isDragging ? 'border-blue-400 bg-blue-50/10' : 'border-foreground/20'
      }`}
    >
      <p className="text-foreground/60">Drag and drop your contract here</p>
      <p className="mt-2 text-sm text-foreground/40">or</p>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="mt-2 rounded-md bg-foreground/10 px-4 py-2 text-sm font-medium hover:bg-foreground/20"
      >
        Browse files
      </button>
      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
      <input
        ref={inputRef}
        type="file"
        aria-label="Upload contract file"
        accept={ALLOWED_EXTENSIONS.join(',')}
        className="hidden"
        onChange={handleInputChange}
      />
    </div>
  );
}
