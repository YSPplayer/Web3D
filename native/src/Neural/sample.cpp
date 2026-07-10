#include <filesystem>
#include "sample.h"
#include "../log.h"
namespace DeepLr::Neural {
	Sample::Sample() {
		labelText = "";
		target = std::array<int, 4>();
	}
    std::shared_ptr<Sample> Sample::Load(const std::string& path, const std::string& imgValue) {
        std::shared_ptr<Sample> sample = std::make_shared<Sample>();
		sample->input = Tensor3D::Load(path);
		sample->target = ParseLabel(imgValue);
		sample->labelText = imgValue;
		return sample;
	}
    std::vector<std::string> Sample::GetPngFiles(const std::string& path) {
        std::vector<std::string> pngFiles;
        if (!std::filesystem::exists(path) || !std::filesystem::is_directory(path)) {
            return pngFiles;
        }
        for (const auto& entry : std::filesystem::directory_iterator(path)) {
            if (!entry.is_regular_file()) continue;
            std::string filename = entry.path().filename().string();
            if (filename.size() < 4) continue;
            std::string ext = filename.substr(filename.size() - 4);
            std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
            if (ext == ".png") {
                pngFiles.push_back(entry.path().string()); // 返回完整路径
            }
        }
        return pngFiles;
    }
	std::vector<std::shared_ptr<Sample>> Sample::Load(const std::string& path) {
        std::vector<std::shared_ptr<Sample>> samples;
        // 检查目录是否存在
        if (!std::filesystem::exists(path) || !std::filesystem::is_directory(path)) {
            Log::Debug("Directory not found: " + path);
            return samples;
        }
        // 遍历目录中的所有文件
        for (const auto& entry : std::filesystem::directory_iterator(path)) {
            if (!entry.is_regular_file()) continue;
            std::string filepath = entry.path().string();
            std::string filename = entry.path().filename().string();
            // 只处理 .png 文件（大小写不敏感）
            if (filename.size() < 4) continue;
            std::string ext = filename.substr(filename.size() - 4);
            std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
            if (ext != ".png") continue;
            // 去掉 .png 后缀，得到 imgValue（如 "0123"）
            std::string imgValue = filename.substr(0, filename.size() - 4);
            // 加载样本
            samples.push_back(Load(filepath, imgValue));
        }
        Log::Debug("Loaded " + std::to_string(samples.size()) + " samples from " + path);
        return samples;
	}
    std::vector<std::shared_ptr<Sample>> Sample::Load(const std::vector<std::string>& filepaths) {
        std::vector<std::shared_ptr<Sample>> samples;
        for (const auto& filepath : filepaths) {
            if (!std::filesystem::exists(filepath) || !std::filesystem::is_regular_file(filepath)) {
                Log::Debug("File not found or not regular file: " + filepath);
                continue;  // 跳过无效文件，继续处理下一个
            }
            // 获取文件名（不含路径），用于提取 imgValue
            std::string filename = std::filesystem::path(filepath).filename().string();
            // 检查扩展名是否为 .png（大小写不敏感）
            if (filename.size() < 4) {
                Log::Debug("Filename too short, skipping: " + filename);
                continue;
            }
            std::string ext = filename.substr(filename.size() - 4);
            std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
            if (ext != ".png") {
                Log::Debug("Not a PNG file, skipping: " + filename);
                continue;
            }
            // 去掉 .png 后缀，得到 imgValue（如 "0123"）
            std::string imgValue = filename.substr(0, filename.size() - 4);
            // 加载样本
            auto sample = Load(filepath, imgValue);  // 假设有 Load(filepath, imgValue) 方法
            if (sample) {
                samples.push_back(sample);
            }
        }
        Log::Debug("Loaded " + std::to_string(samples.size()) + " samples from " +
            std::to_string(filepaths.size()) + " provided file paths");
        return samples;
    }
	std::array<int32_t, 4> Sample::ParseLabel(const std::string& imgValue) {
		if (imgValue.size() != 4) {
			Log::Debug("Expected 4-digit label: " + imgValue);
			return std::array<int32_t, 4>();
		}
		return {
			imgValue[0] - '0',
			imgValue[1] - '0',
			imgValue[2] - '0',
			imgValue[3] - '0'
		};
	}
}