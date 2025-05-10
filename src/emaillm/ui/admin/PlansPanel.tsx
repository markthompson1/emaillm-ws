import React, { useEffect, useState } from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { collection, getDocs, getFirestore } from "firebase/firestore";
import { Button, Box } from "@mui/material";

interface Plan {
  id: string;
  price_cents: number;
  quota_month?: number;
  quota_week?: number;
  features: string[];
}

const columns: GridColDef[] = [
  { field: "id", headerName: "Tier", width: 120 },
  { field: "price_cents", headerName: "Price (¢)", width: 110 },
  { field: "quota_month", headerName: "MonthQuota", width: 120 },
  { field: "quota_week", headerName: "WeekQuota", width: 120 },
  { field: "features", headerName: "Features", width: 200, valueGetter: (params) => params.row.features.join(", ") },
  {
    field: "edit",
    headerName: "Edit",
    width: 100,
    renderCell: () => <Button variant="contained" disabled>Edit</Button>,
    sortable: false,
    filterable: false,
  },
];

export default function PlansPanel() {
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    const fetchPlans = async () => {
      const db = getFirestore();
      const snap = await getDocs(collection(db, "pricing_plans"));
      const docs = snap.docs.map(doc => ({ id: doc.id, ...doc.data() })) as Plan[];
      setPlans(docs);
    };
    fetchPlans();
  }, []);

  return (
    <Box sx={{ height: 400, width: '100%' }}>
      <DataGrid rows={plans} columns={columns} pageSize={5} rowsPerPageOptions={[5]} disableSelectionOnClick />
    </Box>
  );
}
