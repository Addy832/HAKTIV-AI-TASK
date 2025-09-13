"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Control, Evidence } from "./types";
import Snackbar from "./components/Snackbar";
import UploadProgress from "./components/UploadProgress";
import ConfirmationDialog from "./components/ConfirmationDialog";

const API_BASE = "/api";

export default function Home() {
  const [controls, setControls] = useState<Control[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedControl, setSelectedControl] = useState<string>("");
  const [user, setUser] = useState<any>(null);
  const [complianceChecks, setComplianceChecks] = useState<any[]>([]);

  const [snackbar, setSnackbar] = useState({
    message: "",
    type: "info" as "success" | "error" | "info" | "warning",
    isVisible: false,
  });
  const [confirmDialog, setConfirmDialog] = useState({
    isVisible: false,
    title: "",
    message: "",
    onConfirm: () => {},
    type: "danger" as "danger" | "warning" | "info",
    isLoading: false,
  });

  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const showSnackbar = (
    message: string,
    type: "success" | "error" | "info" | "warning" = "info"
  ) => {
    setSnackbar({ message, type, isVisible: true });
  };
  const hideSnackbar = () =>
    setSnackbar((prev) => ({ ...prev, isVisible: false }));
  const showConfirmDialog = (
    title: string,
    message: string,
    onConfirm: () => void,
    type: "danger" | "warning" | "info" = "danger"
  ) => {
    setConfirmDialog({
      isVisible: true,
      title,
      message,
      onConfirm,
      type,
      isLoading: false,
    });
  };
  const hideConfirmDialog = () =>
    setConfirmDialog((prev) => ({ ...prev, isVisible: false }));

  const checkAuth = async () => {
    try {
      // First check if user is authenticated
      const userRes = await fetch(`${API_BASE}/user/`, {
        credentials: "include",
      });
      if (!userRes.ok) {
        // User not authenticated, redirect to login
        router.push("/login");
        return;
      }

      // User is authenticated, load user info and data
      setUser(await userRes.json());
      fetchData();
    } catch (error) {
      console.error("Auth check failed:", error);
      router.push("/login");
    }
  };

  const loadUserInfo = async () => {
    try {
      const res = await fetch(`${API_BASE}/user/`, { credentials: "include" });
      if (res.ok) setUser(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      console.log("Fetching data...");

      const [controlsRes, evidenceRes] = await Promise.all([
        fetch(`${API_BASE}/control/`, { credentials: "include" }),
        fetch(`${API_BASE}/evidence/`, { credentials: "include" }),
      ]);

      console.log("Controls response:", controlsRes.status, controlsRes.ok);
      console.log("Evidence response:", evidenceRes.status, evidenceRes.ok);

      if (!controlsRes.ok || !evidenceRes.ok) {
        const errorMsg = `Failed to fetch data - Controls: ${controlsRes.status}, Evidence: ${evidenceRes.status}`;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      const controlsData = await controlsRes.json();
      const evidenceData = await evidenceRes.json();

      console.log("Controls data:", controlsData);
      console.log("Evidence data:", evidenceData);

      setControls(controlsData);
      setEvidence(evidenceData);
      loadComplianceChecks();
    } catch (err) {
      console.error("Fetch data error:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !selectedControl) return;
    setUploading(true);
    setUploadProgress(0);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) =>
        prev >= 90 ? prev : prev + Math.random() * 10
      );
    }, 200);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("control", selectedControl);
    formData.append("name", selectedFile.name);

    try {
      const res = await fetch(`${API_BASE}/evidence/upload/`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (res.ok) {
        const newEvidence = await res.json();
        setEvidence((prev) => [...prev, newEvidence]);
        setSelectedFile(null);
        setSelectedControl("");
        const fileInput = document.getElementById(
          "file-upload"
        ) as HTMLInputElement;
        if (fileInput) fileInput.value = "";
        setUploadProgress(100);
        showSnackbar("File uploaded and AI analysis completed!", "success");
        // Refresh compliance data to show AI analysis results
        await loadComplianceChecks();
      } else showSnackbar("Upload failed", "error");
    } catch {
      showSnackbar("Upload failed", "error");
    } finally {
      clearInterval(progressInterval);
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const handleDeleteEvidence = (evidenceIds: number[]) => {
    const evidenceNames = evidenceIds
      .map((id) => evidence.find((e) => e.id === id)?.name)
      .filter(Boolean)
      .join(", ");
    showConfirmDialog(
      "Delete Evidence",
      `Are you sure you want to delete ${evidenceNames}?`,
      () => confirmDeleteEvidence(evidenceIds),
      "danger"
    );
  };

  const confirmDeleteEvidence = async (evidenceIds: number[]) => {
    // Show loading state
    setConfirmDialog((prev) => ({ ...prev, isLoading: true }));

    try {
      const res = await fetch(`${API_BASE}/evidence/delete/`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ids: evidenceIds }),
      });
      if (res.ok) {
        setEvidence((prev) => prev.filter((e) => !evidenceIds.includes(e.id)));
        showSnackbar("Evidence deleted", "success");
        // Close dialog on success
        hideConfirmDialog();
      } else {
        showSnackbar("Failed to delete evidence", "error");
        // Hide loading state on error but keep dialog open
        setConfirmDialog((prev) => ({ ...prev, isLoading: false }));
      }
    } catch {
      showSnackbar("Failed to delete evidence", "error");
      // Hide loading state on error but keep dialog open
      setConfirmDialog((prev) => ({ ...prev, isLoading: false }));
    }
  };

  const handleLogout = async () => {
    try {
      const res = await fetch(`${API_BASE}/logout/`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      window.location.href = data.logout_url || "/login";
    } catch {
      router.push("/login");
    }
  };

  const loadComplianceChecks = async () => {
    try {
      const res = await fetch(`${API_BASE}/compliance/checks/`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        console.log("Compliance checks loaded:", data);
        setComplianceChecks(data.compliance_checks || []);
      }
    } catch {
      console.error("Failed to load compliance checks");
    }
  };

  const getComplianceStatus = (evidenceId: number) =>
    complianceChecks.find((c) => c.evidence_id === evidenceId)?.status;

  const getComplianceDetails = (evidenceId: number) =>
    complianceChecks.find((c) => c.evidence_id === evidenceId);
  const getComplianceStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-green-500/20 text-green-400 border border-green-500/30";
      case "rejected":
        return "bg-red-500/20 text-red-400 border border-red-500/30";
      case "processing":
        return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
      case "error":
        return "bg-gray-500/20 text-gray-400 border border-gray-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border border-gray-500/30";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div className="text-xl text-white">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">Error: {error}</div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg
                  className="w-4 h-4 sm:w-6 sm:h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-lg sm:text-2xl font-bold text-white truncate">
                  HAKTIV AI - Compliance System
                </h1>
                <p className="text-xs sm:text-sm text-gray-400 truncate">
                  Welcome back, {user?.first_name || user?.email || "User"} (
                  {user?.company})
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="px-3 py-2 sm:px-4 sm:py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800 flex items-center"
            >
              <svg
                className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              <span className="text-xs sm:text-sm">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Evidence Management Section */}
        <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 space-y-4 sm:space-y-0">
            <div>
              <h2 className="text-xl sm:text-2xl font-semibold text-white flex items-center mb-2">
                <svg
                  className="w-5 h-5 sm:w-6 sm:h-6 mr-2 sm:mr-3 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Evidence Management
              </h2>
              <p className="text-gray-400 text-sm">
                Upload and manage compliance evidence for your company
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">
                {evidence.length}
              </div>
              <div className="text-sm text-gray-400">Total Files</div>
            </div>
          </div>

          {/* Upload Form */}
          <div className="mb-6 sm:mb-8 p-4 sm:p-6 bg-gradient-to-r from-gray-700 to-gray-600 rounded-lg border border-gray-500">
            <h3 className="font-semibold text-white mb-3 sm:mb-4 flex items-center text-base sm:text-lg">
              <svg
                className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Upload New Evidence
            </h3>
            <form
              onSubmit={handleFileUpload}
              className="space-y-3 sm:space-y-4"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-200 mb-1 sm:mb-2">
                    Select Control
                  </label>
                  <select
                    value={selectedControl}
                    onChange={(e) => setSelectedControl(e.target.value)}
                    className="w-full bg-gray-600 border border-gray-500 rounded-lg px-2 sm:px-3 py-2 sm:py-3 text-white text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">
                      Choose a control to upload evidence for
                    </option>
                    {controls.map((control) => (
                      <option key={control.id} value={control.id}>
                        {control.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-200 mb-1 sm:mb-2">
                    Select File
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    onChange={(e) =>
                      setSelectedFile(e.target.files?.[0] || null)
                    }
                    className="w-full bg-gray-600 border border-gray-500 rounded-lg px-2 sm:px-3 py-2 sm:py-3 text-white text-xs sm:text-sm file:mr-2 sm:file:mr-4 file:py-1 sm:file:py-2 file:px-2 sm:file:px-4 file:rounded-full file:border-0 file:text-xs sm:file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    accept="image/*,.pdf,.doc,.docx"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={uploading || !selectedFile || !selectedControl}
                  className="px-4 py-2 sm:px-6 sm:py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center font-medium text-xs sm:text-sm"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 sm:h-4 sm:w-4 border-b-2 border-white mr-1 sm:mr-2"></div>
                      <span className="text-xs sm:text-sm">Uploading...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <span className="text-xs sm:text-sm">
                        Upload Evidence
                      </span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Evidence List */}
          <div className="space-y-3 sm:space-y-4">
            {evidence.length === 0 ? (
              <div className="text-center py-8 sm:py-12">
                <svg
                  className="w-12 h-12 sm:w-16 sm:h-16 text-gray-500 mx-auto mb-3 sm:mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="text-base sm:text-lg font-medium text-gray-400 mb-2">
                  No Evidence Uploaded
                </h3>
                <p className="text-sm sm:text-base text-gray-500">
                  Upload your first evidence file to get started
                </p>
              </div>
            ) : (
              evidence.map((item) => {
                const complianceStatus = getComplianceStatus(item.id);
                const complianceDetails = getComplianceDetails(item.id);
                const isRejected = complianceStatus === "rejected";
                const isApproved = complianceStatus === "approved";
                const isProcessing = complianceStatus === "processing";

                // Debug logging
                console.log(`Evidence ${item.id}:`, {
                  complianceStatus,
                  complianceDetails,
                  hasAiAnalysis: complianceDetails?.ai_analysis,
                  aiAnalysis: complianceDetails?.ai_analysis,
                });

                return (
                  <div
                    key={item.id}
                    className={`rounded-lg p-4 sm:p-6 border transition-all duration-200 ${
                      isRejected
                        ? "bg-red-900/20 border-red-500/30 hover:border-red-400/50"
                        : isApproved
                        ? "bg-green-900/20 border-green-500/30 hover:border-green-400/50"
                        : isProcessing
                        ? "bg-yellow-900/20 border-yellow-500/30 hover:border-yellow-400/50"
                        : "bg-gray-700 border-gray-600 hover:border-gray-500"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start space-y-3 sm:space-y-0">
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:items-center mb-3 space-y-2 sm:space-y-0">
                          <h3 className="font-semibold text-white text-base sm:text-lg mr-0 sm:mr-4 truncate">
                            {item.name}
                          </h3>
                          <div className="flex items-center gap-2 flex-wrap">
                            {/* Evidence Status */}
                            <span
                              className={`px-2 py-1 sm:px-3 sm:py-1 rounded-full text-xs sm:text-sm font-medium ${
                                item.status === "approved"
                                  ? "bg-green-500/20 text-green-400 border border-green-500/30"
                                  : item.status === "rejected"
                                  ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                  : "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                              }`}
                            >
                              {item.status}
                            </span>

                            {/* AI Compliance Status */}
                            {complianceStatus && (
                              <span
                                className={`px-2 py-1 sm:px-3 sm:py-1 rounded-full text-xs sm:text-sm font-medium ${getComplianceStatusColor(
                                  complianceStatus
                                )}`}
                              >
                                AI: {complianceStatus}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-3 sm:mb-4">
                          <div>
                            <p className="text-xs sm:text-sm text-gray-400 mb-1">
                              Control
                            </p>
                            <p className="text-white font-medium text-sm sm:text-base">
                              {controls.find((c) => c.id === item.control)
                                ?.name || "Unknown"}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm text-gray-400 mb-1">
                              Uploaded
                            </p>
                            <p className="text-white text-sm sm:text-base">
                              {new Date(item.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        {item.file && (
                          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
                            <a
                              href={`http://localhost:8000${item.file}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors font-medium text-sm"
                            >
                              <svg
                                className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                />
                              </svg>
                              <span className="text-xs sm:text-sm">
                                View File
                              </span>
                            </a>
                          </div>
                        )}

                        {/* Compliance Analysis Details - Always show for evidence items */}
                        {item.file && (
                          <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-600">
                            <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center">
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                                />
                              </svg>
                              AI Analysis Results
                            </h4>

                            {/* Basic Status */}
                            <div className="mb-3">
                              <span className="text-sm text-gray-400">
                                Status:{" "}
                              </span>
                              <span
                                className={`font-medium ${
                                  complianceDetails?.status === "approved" ||
                                  item.status === "approved"
                                    ? "text-green-400"
                                    : complianceDetails?.status ===
                                        "rejected" || item.status === "rejected"
                                    ? "text-red-400"
                                    : "text-yellow-400"
                                }`}
                              >
                                {complianceDetails?.status === "approved" ||
                                item.status === "approved"
                                  ? "Approved"
                                  : complianceDetails?.status === "rejected" ||
                                    item.status === "rejected"
                                  ? "Rejected"
                                  : "Processing"}
                              </span>
                            </div>

                            {/* AI Analysis Details (if available) */}
                            {complianceDetails?.ai_analysis && (
                              <>
                                <div className="mb-3">
                                  <span className="text-sm text-gray-400">
                                    AI Result:{" "}
                                  </span>
                                  <span
                                    className={`font-medium ${
                                      complianceDetails.ai_analysis.is_compliant
                                        ? "text-green-400"
                                        : "text-red-400"
                                    }`}
                                  >
                                    {complianceDetails.ai_analysis.is_compliant
                                      ? "Compliant"
                                      : "Non-Compliant"}
                                  </span>
                                  <span className="ml-2 text-sm text-gray-500">
                                    (Confidence:{" "}
                                    {Math.round(
                                      (complianceDetails.ai_analysis
                                        .confidence || 0) * 100
                                    )}
                                    %)
                                  </span>
                                </div>

                                {/* Detected Elements */}
                                {complianceDetails.ai_analysis
                                  .detected_elements &&
                                  complianceDetails.ai_analysis
                                    .detected_elements.length > 0 && (
                                    <div className="mb-3">
                                      <span className="text-sm text-gray-400">
                                        Detected Elements:
                                      </span>
                                      <div className="flex flex-wrap gap-2 mt-1">
                                        {complianceDetails.ai_analysis.detected_elements.map(
                                          (element: string, index: number) => (
                                            <span
                                              key={index}
                                              className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full border border-blue-500/30"
                                            >
                                              {element}
                                            </span>
                                          )
                                        )}
                                      </div>
                                    </div>
                                  )}

                                {/* Reasoning */}
                                {complianceDetails.ai_analysis.reasoning && (
                                  <div className="mb-3">
                                    <span className="text-sm text-gray-400">
                                      Analysis:
                                    </span>
                                    <p className="text-sm text-gray-300 mt-1">
                                      {complianceDetails.ai_analysis.reasoning}
                                    </p>
                                  </div>
                                )}
                              </>
                            )}

                            {/* Show processing message if no AI analysis yet */}
                            {!complianceDetails?.ai_analysis &&
                              complianceDetails?.status === "processing" && (
                                <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                                  <span className="text-sm font-medium text-yellow-400">
                                    AI analysis in progress...
                                  </span>
                                  <p className="text-sm text-yellow-300 mt-1">
                                    Please wait while our AI analyzes your
                                    evidence.
                                  </p>
                                </div>
                              )}

                            {/* Show error message if AI analysis failed */}
                            {complianceDetails?.status === "error" && (
                              <div className="mb-3 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                                <span className="text-sm font-medium text-red-400">
                                  AI analysis failed
                                </span>
                                <p className="text-sm text-red-300 mt-1">
                                  {complianceDetails?.rejection_reason ||
                                    "Unable to analyze the evidence. Please try uploading again."}
                                </p>
                              </div>
                            )}

                            {/* Show message if no compliance details available */}
                            {!complianceDetails && (
                              <div className="mb-3 p-3 bg-gray-700/20 border border-gray-500/30 rounded-lg">
                                <span className="text-sm font-medium text-gray-400">
                                  Compliance check pending
                                </span>
                                <p className="text-sm text-gray-300 mt-1">
                                  Compliance analysis will be performed shortly.
                                </p>
                              </div>
                            )}

                            {/* Rejection Reason (if rejected) */}
                            {(isRejected || item.status === "rejected") &&
                              complianceDetails?.rejection_reason && (
                                <div className="mb-3 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                                  <span className="text-sm font-medium text-red-400">
                                    Rejection Reason:
                                  </span>
                                  <p className="text-sm text-red-300 mt-1">
                                    {complianceDetails?.rejection_reason}
                                  </p>
                                </div>
                              )}

                            {/* Recommendations */}
                            {complianceDetails?.recommendations && (
                              <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                                <span className="text-sm font-medium text-blue-400">
                                  Recommendations:
                                </span>
                                <p className="text-sm text-blue-300 mt-1">
                                  {complianceDetails?.recommendations}
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="ml-3 sm:ml-6">
                        <button
                          onClick={() => handleDeleteEvidence([item.id])}
                          className="p-1.5 sm:p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
                          title="Delete evidence"
                        >
                          <svg
                            className="w-4 h-4 sm:w-5 sm:h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </main>

      {/* Components */}
      <Snackbar
        message={snackbar.message}
        type={snackbar.type}
        isVisible={snackbar.isVisible}
        onClose={hideSnackbar}
      />

      <UploadProgress
        isVisible={uploading}
        progress={uploadProgress}
        fileName={selectedFile?.name || ""}
      />

      <ConfirmationDialog
        isVisible={confirmDialog.isVisible}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={confirmDialog.onConfirm}
        onCancel={hideConfirmDialog}
        type={confirmDialog.type}
        isLoading={confirmDialog.isLoading}
      />
    </div>
  );
}
