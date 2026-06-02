import { createHashRouter } from "react-router-dom";
import { Layout } from "../components/Layout";
import { AboutPage } from "../pages/AboutPage";
import { HomePage } from "../pages/HomePage";
import { MajorDetailPage } from "../pages/MajorDetailPage";
import { MajorsPage } from "../pages/MajorsPage";
import { RecommendPlaceholderPage } from "../pages/RecommendPlaceholderPage";
import { SchoolDetailPage } from "../pages/SchoolDetailPage";
import { SchoolsPage } from "../pages/SchoolsPage";
import { WishlistPage } from "../pages/WishlistPage";

export const router = createHashRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "schools", element: <SchoolsPage /> },
      { path: "schools/:schoolId", element: <SchoolDetailPage /> },
      { path: "majors", element: <MajorsPage /> },
      { path: "majors/:majorId", element: <MajorDetailPage /> },
      { path: "wishlist", element: <WishlistPage /> },
      { path: "recommend", element: <RecommendPlaceholderPage /> },
      { path: "about", element: <AboutPage /> },
    ],
  },
]);
