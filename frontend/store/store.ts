import { configureStore } from "@reduxjs/toolkit";

import { documentsApi } from "@/features/documents/api";

export const store = configureStore({
  reducer: {
    [documentsApi.reducerPath]: documentsApi.reducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(documentsApi.middleware)
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
