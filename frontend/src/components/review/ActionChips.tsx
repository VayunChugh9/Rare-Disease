interface ActionChipsProps {
  items: string[];
}

export function ActionChips({ items }: ActionChipsProps) {
  if (items.length === 0) return null;

  return (
    <div className="flex gap-3 mx-6 mb-6 flex-wrap">
      {items.map((item, i) => (
        <button
          key={i}
          className="px-4 py-1.5 rounded-full border border-[#0D9488]/30 text-[#0D9488] text-xs font-bold uppercase tracking-wider hover:bg-[#0D9488] hover:text-white transition-all duration-150"
        >
          {item}
        </button>
      ))}
    </div>
  );
}
