'use client';

import { useState } from 'react';
import { FileDropZone } from './FileDropZone';

interface SubmitPayload {
  file: File;
  fileName: string;
  fileSize: number;
  fileType: string;
  instructions: string;
}

function handleSubmit(payload: SubmitPayload) {
  console.log(payload);
}

export default function EvaluateContractPage() {
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState('');

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-3xl font-bold tracking-tight">Evaluate Contract</h1>

      <div className="mt-8">
        <FileDropZone onFileChange={setFile} />
      </div>

      <div className="mt-6">
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Add any specific instructions for the evaluation..."
          rows={4}
          className="w-full rounded-lg border border-foreground/20 bg-transparent px-4 py-3 text-sm placeholder:text-foreground/40 focus:border-foreground/40 focus:outline-none"
        />
      </div>

      <div className="mt-6">
        <button
          type="button"
          disabled={!file}
          onClick={() => {
            if (!file) return;
            const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
            handleSubmit({
              file,
              fileName: file.name,
              fileSize: file.size,
              fileType: ext,
              instructions,
            });
          }}
          className="rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background disabled:opacity-40"
        >
          Evaluate Contract
        </button>
      </div>
    </div>
  );
}
