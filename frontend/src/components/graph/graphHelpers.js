export const buildFolderData = (raw_ast) => {
  if (!raw_ast?.files) return [];
  const folderMap = {};
  Object.entries(raw_ast.files).forEach(([filePath, fileData]) => {
    const parts = filePath.split('/');
    const folderKey = parts.length > 1 ? parts[0] : '__root__';
    if (!folderMap[folderKey]) {
      folderMap[folderKey] = {
        key: folderKey,
        label: folderKey === '__root__' ? '/ (root)' : folderKey,
        shortLabel: folderKey === '__root__' ? 'root' : folderKey,
        files: [],
      };
    }
    const functions = fileData?.functions || {};
    folderMap[folderKey].files.push({
      path: filePath,
      name: parts[parts.length - 1],
      functions,
      functionCount: Object.keys(functions).length,
      dependsOn: fileData.depends_on || [],
      isEntry: raw_ast.entry_point === filePath,
    });
  });
  return Object.values(folderMap).sort((a, b) => a.label.localeCompare(b.label));
};

export const buildFileData = (raw_ast) => {
  if (!raw_ast?.files) return [];
  return Object.entries(raw_ast.files).map(([filePath, fileData]) => {
    const parts = filePath.split('/');
    return {
      path: filePath,
      name: parts[parts.length - 1],
      folderKey: parts.length > 1 ? parts[0] : '__root__',
      functions: fileData?.functions || {},
      functionCount: Object.keys(fileData?.functions || {}).length,
      dependsOn: fileData?.depends_on || [],
      imports: fileData?.imports || [],
      entry: fileData?.entry || false,
      source: fileData?.source || '',
    };
  });
};
