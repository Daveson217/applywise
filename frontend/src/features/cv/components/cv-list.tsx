import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import {
  FileText,
  Loader2,
  MoreHorizontal,
  Star,
  Trash2,
  Upload,
} from "lucide-react";
import { useRef, useState } from "react";

import { useCVVersions, useDeleteCV, useSetDefaultCV, useUploadCV } from "../hooks";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function CVList() {
  const { data, isLoading } = useCVVersions();
  const uploadMutation = useUploadCV();
  const deleteMutation = useDeleteCV();
  const setDefaultMutation = useSetDefaultCV();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadName, setUploadName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const versions = data?.results || [];

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!uploadName) {
        setUploadName(file.name.replace(/\.(pdf|docx)$/i, ""));
      }
    }
  }

  async function handleUpload() {
    if (!selectedFile || !uploadName.trim()) return;
    await uploadMutation.mutateAsync({ name: uploadName.trim(), file: selectedFile });
    setSelectedFile(null);
    setUploadName("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Upload Resume</CardTitle>
          <CardDescription>
            Upload a PDF or DOCX file. Text will be extracted automatically.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 sm:flex-row">
            <div className="flex-1 space-y-2">
              <Label>Version Name</Label>
              <Input
                placeholder="e.g. SWE Resume v2"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
              />
            </div>
            <div className="flex items-end gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={handleFileChange}
              />
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="mr-2 h-4 w-4" />
                {selectedFile ? selectedFile.name : "Choose File"}
              </Button>
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || !uploadName.trim() || uploadMutation.isPending}
              >
                {uploadMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Upload
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))
        ) : versions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
              <p className="text-lg font-medium text-muted-foreground">
                No resumes uploaded yet
              </p>
              <p className="text-sm text-muted-foreground">
                Upload your resume to get started with ATS scoring and cover
                letter generation.
              </p>
            </CardContent>
          </Card>
        ) : (
          versions.map((cv) => (
            <Card key={cv.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{cv.name}</span>
                      {cv.is_default && (
                        <Badge variant="secondary" className="text-xs">
                          <Star className="mr-1 h-3 w-3" />
                          Default
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(cv.file_size)} &middot;{" "}
                      {format(new Date(cv.created_at), "MMM d, yyyy")}
                    </p>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {!cv.is_default && (
                      <DropdownMenuItem
                        onClick={() => setDefaultMutation.mutate(cv.id)}
                      >
                        <Star className="mr-2 h-4 w-4" />
                        Set as Default
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => deleteMutation.mutate(cv.id)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
