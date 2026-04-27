import { InboxOutlined } from "@ant-design/icons";
import { Upload, message } from "antd";
import type { RcFile } from "antd/es/upload";

import type { DocType } from "../../types/knowledge";
import { uploadDocument } from "../../api/knowledge";

interface DocUploaderProps {
  docType: DocType;
  onUploaded: () => void;
}

export function DocUploader({ docType, onUploaded }: DocUploaderProps): JSX.Element {
  return (
    <Upload.Dragger
      multiple
      showUploadList={false}
      customRequest={async ({ file, onSuccess, onError }) => {
        try {
          await uploadDocument(file as File, docType);
          message.success("文档已上传，正在后台解析与建索引。");
          onSuccess?.("ok");
          onUploaded();
        } catch (error) {
          const nextError = error instanceof Error ? error : new Error("上传失败。");
          message.error(nextError.message);
          onError?.(nextError);
        }
      }}
      beforeUpload={(file: RcFile) => {
        const allowed = [".pdf", ".docx", ".txt", ".xlsx", ".csv"];
        const valid = allowed.some((suffix) => file.name.toLowerCase().endsWith(suffix));
        if (!valid) {
          message.warning("仅支持上传 PDF、DOCX、TXT、XLSX、CSV。");
        }
        return valid || Upload.LIST_IGNORE;
      }}
      style={{
        borderRadius: 16,
        border: "1px dashed rgba(35, 75, 73, 0.28)",
        background: "rgba(244, 249, 243, 0.72)"
      }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined style={{ color: "#216f6a" }} />
      </p>
      <p className="ant-upload-text">拖拽文档到这里，或点击上传</p>
      <p className="ant-upload-hint">上传后系统会自动解析、分块、向量化并建立混合检索索引。</p>
    </Upload.Dragger>
  );
}
