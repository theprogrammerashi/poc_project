import React from "react";
import { Trash2 } from "lucide-react";

interface DeleteConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

export default function DeleteConfirmationModal({ isOpen, onClose, onConfirm }: DeleteConfirmationModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl w-full max-w-[320px] p-6 shadow-2xl border border-red-500/20 relative animate-in fade-in zoom-in duration-200">
                {/* Red outline based on design "DELETE CONFIRMATION" */}
                <div className="absolute inset-x-4 inset-y-4 border border-[#FCA5A5] rounded-2xl pointer-events-none" />

                <div className="relative z-10">
                    <div className="flex items-start gap-4 mb-3">
                         <div className="text-[#DC2626] mt-1">
                             <Trash2 size={24} strokeWidth={2} />
                         </div>
                         <h3 className="text-[18px] font-bold text-[#DC2626] leading-tight pr-4">
                             Remove this conversation?
                         </h3>
                    </div>

                    <p className="text-[14px] text-text-secondary leading-[1.6] mb-8 pr-2">
                        This conversation and all its content will be permanently removed. This cannot be undone.
                    </p>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 py-3 px-4 rounded-xl border border-gray-200 text-text-primary font-semibold text-[15px] hover:bg-gray-50 transition-colors"
                        >
                            Keep it
                        </button>
                        <button
                            onClick={onConfirm}
                            className="flex-1 py-3 px-4 rounded-xl bg-[#DC2626] text-white font-semibold text-[15px] hover:bg-red-700 transition-colors shadow-sm"
                        >
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
