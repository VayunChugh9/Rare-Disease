import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ReferralQueue } from "./components/queue/ReferralQueue";
import { UploadPanel } from "./components/upload/UploadPanel";
import { ReviewWorkspace } from "./components/review/ReviewWorkspace";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<ReferralQueue />} />
          <Route path="upload" element={<UploadPanel />} />
          <Route path="review/:id" element={<ReviewWorkspace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
