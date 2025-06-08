import React from "react";

function LargePopup({ isOpen, onClose, children }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-white w-[90%] h-[90%] p-8 rounded-lg shadow-2xl overflow-y-auto relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-700 hover:text-black text-2xl font-bold"
        >
          ×
        </button>
        {children}
      </div>
    </div>
  );
}

export default LargePopup;
