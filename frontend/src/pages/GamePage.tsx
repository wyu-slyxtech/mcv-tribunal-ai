import { useParams } from "react-router-dom";

export default function GamePage() {
  const { id } = useParams();
  return <div className="p-8 text-white bg-gray-950 min-h-screen">Game: {id}</div>;
}
