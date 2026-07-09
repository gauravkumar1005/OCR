import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import UploadPage from "./pages/UploadPage.jsx";
import StatusPage from "./pages/StatusPage.jsx";
import ClaimsListPage from "./pages/ClaimsListPage.jsx";
import DocumentDataPage from "./pages/DocumentDataPage.jsx";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/status/:claimId" element={<StatusPage />} />
        <Route path="/claims" element={<ClaimsListPage />} />
        <Route path="/claims/:claimId" element={<DocumentDataPage />} />
      </Routes>
    </Layout>
  );
}
