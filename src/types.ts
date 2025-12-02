export interface API {
  name: string;
  description: string;
  link: string;
  category?: string;
  auth?: string;
  https?: boolean;
  cors?: string;
}

export interface FavoriteState {
  [key: string]: boolean;
}
