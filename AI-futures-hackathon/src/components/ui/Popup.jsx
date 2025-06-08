import React, { useState } from 'react';

   function Popup({ isOpen, onClose, children }) {
     if (!isOpen) return null;

     return (
       <div className="absolute top-0 right-0 inset-0 bg-gray-500 bg-opacity-15 flex items-center justify-center">
         <div className="absolute top-3 right-3 bg-white p-6 rounded-lg shadow-xl">
           <button onClick={onClose} className="absolute top-2 right-2 text-gray-600 hover:text-gray-800">
             x
           </button>
           {children}
         </div>
       </div>
     );
   }

   export default Popup;