"use client";

import { useState, useEffect } from "react";

interface UploadProgressProps {
  isVisible: boolean;
  progress: number;
  fileName: string;
  onCancel?: () => void;
}

export default function UploadProgress({
  isVisible,
  progress,
  fileName,
  onCancel,
}: UploadProgressProps) {
  const [displayProgress, setDisplayProgress] = useState(0);

  useEffect(() => {
    if (isVisible) {
      // Animate progress bar
      const timer = setInterval(() => {
        setDisplayProgress((prev) => {
          if (prev >= progress) {
            clearInterval(timer);
            return progress;
          }
          return prev + 1;
        });
      }, 20);

      return () => clearInterval(timer);
    } else {
      setDisplayProgress(0);
    }
  }, [isVisible, progress]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Uploading File</h3>
          {onCancel && (
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          )}
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-300 mb-2 truncate">{fileName}</p>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${displayProgress}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1 text-right">
            {displayProgress}%
          </p>
        </div>

        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
        </div>
      </div>
    </div>
  );
}
