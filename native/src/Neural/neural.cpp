#include <cmath>
#include <format>
#include <fstream>
#include "neural.h"
#include "conv2d.h"
#include "relu.h"
#include "maxpool.h"
#include "flatten.h"
#include "linear.h"
#include "softmax.h"
#include "../log.h"
#include <thread>
#include <chrono>
#define WRITE_TO_BUFFER(buf, obj) \
    buf.insert(buf.end(), \
        reinterpret_cast<const char*>(&(obj)), \
        reinterpret_cast<const char*>(&(obj)) + sizeof(obj))
#define PARSE_BUFFER(buf, offset, obj) \
    do { \
        std::memcpy(&(obj), (buf).data() + (offset), sizeof(obj)); \
        (offset) += sizeof(obj); \
    } while(0)
namespace DeepLr::Neural {
	std::shared_ptr<std::mt19937> Neural::g = std::make_shared<std::mt19937>(42);
	Neural::Neural(TensorShape tensorShape, const std::vector<NeuralBuild>& builds) {
		this->inputShape = tensorShape;
		SetBuilds(builds);
	}
	Neural::Neural() {
	}
	std::shared_ptr<Neural> Neural::BuildDefaultNeural() {
		std::vector<NeuralBuild> builds = {
			NeuralBuild(NeuralType::Conv2D, 8, 128, 128),
				NeuralBuild(NeuralType::RelU, 8, 128, 128),
				NeuralBuild(NeuralType::MaxPool, 8, 64, 64),
				NeuralBuild(NeuralType::Conv2D, 16, 64, 64),
				NeuralBuild(NeuralType::RelU, 16, 64, 64),
				NeuralBuild(NeuralType::MaxPool, 16, 32, 32),
				NeuralBuild(NeuralType::Conv2D, 24, 32, 32),
				NeuralBuild(NeuralType::RelU, 24, 32, 32),
				NeuralBuild(NeuralType::MaxPool, 24, 16, 16),
				NeuralBuild(NeuralType::Conv2D, 32, 16, 16),
				NeuralBuild(NeuralType::RelU, 32, 16, 16),
				NeuralBuild(NeuralType::MaxPool, 32, 8, 8),
				NeuralBuild(NeuralType::Flatten, 1, 1, 2048),
				NeuralBuild(NeuralType::Linear, 1, 1, 64),
				NeuralBuild(NeuralType::RelU, 1, 1, 64),
				NeuralBuild(NeuralType::Linear, 1, 1, 40),
				NeuralBuild(NeuralType::SoftMax, 1, 10, 4),
		};
		TensorShape shape = { 1,128,128 };
		return std::make_shared<Neural>(shape, builds);
	}
	bool Neural::Predict(const Tensor3D& input, Tensor3D& output,const std::string& filename) {
		std::vector<char> buffer;
		if (!ReadFromBinaryFile(filename, buffer)) {
			Log::Debug("Failed to load the binary file.");
			return false;
		} 
		int32_t offset = 0;
		ModelHeader header;
		PARSE_BUFFER(buffer,offset,header.magic);
		const char* keyMagic = KEY_MAGIC;
		for (int32_t i = 0; i < 8; ++i) {
			if (header.magic[i] != keyMagic[i]) {
				Log::Debug("Failed to parse model file format.");
				return false;
			}
		}
		PARSE_BUFFER(buffer, offset, header.version);
		if (header.version != KEY_VERSION) {
			Log::Debug("Failed to parse model file format.");
			return false;
		}
		PARSE_BUFFER(buffer, offset, header.fileType);
		if (header.fileType != KEY_TYPE_MODEL) {
			Log::Debug("Failed to parse model file format.");
			return false;
		}
		std::vector<NeuralBuild> builds;
		std::vector<std::any> cores;
		//网络层数
		int32_t buildSize = 0;
		PARSE_BUFFER(buffer, offset, buildSize);
		builds.resize(buildSize);
		cores.resize(buildSize);
		//输入层数
		TensorShape shape;
		PARSE_BUFFER(buffer, offset, shape.c);
		PARSE_BUFFER(buffer, offset, shape.w);
		PARSE_BUFFER(buffer, offset, shape.h);
		if (shape.c != input.Channel() || shape.w != input.Width() || shape.h != input.Height()) {
			Log::Debug(std::format("Model parameter mismatch.model shape:[{},{},{}],input shape:[{},{},{}].",
				shape.c, shape.w, shape.h, input.Channel(), input.Width(), input.Height()));
			return false;
		}
		for (int32_t i = 0; i < buildSize; ++i) {
			int32_t type = 0;
			int32_t c = 0;
			int32_t w = 0;
			int32_t h = 0;
			PARSE_BUFFER(buffer, offset, type);
			PARSE_BUFFER(buffer, offset, c);
			PARSE_BUFFER(buffer, offset, w);
			PARSE_BUFFER(buffer, offset, h);
			builds[i] = NeuralBuild((NeuralType)type,c,w,h);
			if (type == NeuralType::Conv2D) {
				std::pair<std::vector<Tensor3D>, Tensor3D> coreData;
				int32_t ksize = 0;
				PARSE_BUFFER(buffer, offset, ksize);
				for (int32_t j = 0; j < ksize; ++j) {
					coreData.first.push_back(ReadTensor3D(buffer, offset));
				}
				coreData.second = ReadTensor3D(buffer, offset);
				cores[i] = std::move(coreData);
			}
			else if (type == NeuralType::Linear) {
				std::pair<Tensor3D, Tensor3D> coreData;
				coreData.first = ReadTensor3D(buffer, offset);
				coreData.second = ReadTensor3D(buffer, offset);
				cores[i] = std::move(coreData);
			}
		}
		output = Predict(input,builds,cores);
		return true;
	}
	Tensor3D Neural::Predict(const Tensor3D& input) {
		Tensor3D tensor3d = input;
		for (int32_t j = 0; j < neural.size(); ++j) {
			Layer* layer = neural[j];
			if (!layer) continue;
			//向前传播
			tensor3d = layer->Forward(tensor3d);
		}
		return tensor3d;
	}
	Tensor3D Neural::Predict(const Tensor3D& input,const std::vector<NeuralBuild>& builds, const std::vector<std::any>& cores) {
		inputShape = { input.Channel(),input.Width(),input.Height() };
		SetBuilds(builds);
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (layer->GetNeuralType() == NeuralType::Conv2D) {
				const auto& data = std::any_cast<std::pair<std::vector<Tensor3D>, Tensor3D>>(cores[i]);
				Conv2D* conv2d =  dynamic_cast<Conv2D*>(layer);
				conv2d->SetKernels(data.first);
				conv2d->SetBias(data.second);

			}
			else if (layer->GetNeuralType() == NeuralType::Linear) {
				const auto& data = std::any_cast<std::pair<Tensor3D, Tensor3D>>(cores[i]);
				Linear* linear = dynamic_cast<Linear*>(layer);
				linear->SetW(data.first);
				linear->SetB(data.second);
			}
		}
		return Predict(input);
	}
	float Neural::TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples, float lr) {
		if (samples.size() <= 0) return 0.0f;
		float totalLoss = 0.0f;
		float batchLoss = 0.0f;
		bool debugBatch = samples.size() <= 8;

		for (int32_t i = 0; i < samples.size(); ++i) { //批量训练
			const auto& sample = samples.at(i);
			Tensor3D tensor3d = *sample->Data();
			if (debugBatch) {
				Log::Debug(std::format(
					"debug input sample={},target={}{}{}{},shape=[{},{},{}],min={},max={}",
					i,
					(*sample->Target())[0], (*sample->Target())[1], (*sample->Target())[2], (*sample->Target())[3],
					tensor3d.Channel(), tensor3d.Width(), tensor3d.Height(),
					tensor3d.Min(), tensor3d.Max()));
			}
			for (int32_t j = 0; j < neural.size(); ++j) {
				Layer* layer = neural[j];
				if (!layer) continue;
				//向前传播
				tensor3d = layer->Forward(tensor3d);
			}
			float sampleLoss = loss.Forward(tensor3d, *sample->Target());
			totalLoss += sampleLoss;
			if (debugBatch) {
				Log::Debug(std::format(
					"debug forward sample={},loss={},outShape=[{},{},{}],probMin={},probMax={},targetProbMean={}",
					i,
					sampleLoss,
					tensor3d.Channel(), tensor3d.Width(), tensor3d.Height(),
					tensor3d.Min(), tensor3d.Max(),
					tensor3d.TargetProbMean(*sample->Target())));
			}
			//向后传播
			for (int32_t j = neural.size() - 1; j >= 0; --j) {
				Layer* layer = neural[j];
				if (!layer) continue;
				tensor3d = layer->Backward(tensor3d, *sample->Target());
			}
		}
		batchLoss = totalLoss / samples.size();
		//更新梯度
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (!layer) continue;
			layer->Update(lr, samples.size());
		}
		return batchLoss;
	}
	void Neural::Crear() {
		for (int32_t i = 0; i < neural.size(); ++i) {
			if (neural[i]) {
				delete neural[i];
			} 
			neural[i] = nullptr;
		}
		neural.clear();
	}
	void Neural::SetBuilds(const std::vector<NeuralBuild>& builds) {
		Crear();
		neural.resize(builds.size());
		TensorShape lastshape = inputShape;
		for (int32_t i = 0; i < builds.size(); ++i) {
			auto& build = builds[i];
			neural[i] = nullptr;
			TensorShape shape = { build.c,build.w,build.h };
			if (build.type == NeuralType::Conv2D) neural[i] = new Conv2D();
			else if (build.type == NeuralType::RelU) neural[i] = new Relu();
			else if (build.type == NeuralType::MaxPool) neural[i] = new MaxPool();
			else if (build.type == NeuralType::Flatten) neural[i] = new Flatten();
			else if (build.type == NeuralType::Linear) neural[i] = new Linear();
			else if (build.type == NeuralType::SoftMax) neural[i] = new SoftMax();
			neural[i]->SetShape(lastshape, shape);
			lastshape = shape;
		}
	}
	void Neural::WriteTensor3D(const Tensor3D& tensor, std::vector<char>& buffer) {
		const std::vector<float>& tdata = tensor.Data();
		int32_t c = tensor.Channel();
		int32_t w = tensor.Width();
		int32_t h = tensor.Height();
		//先写入shape，最后写值
		WRITE_TO_BUFFER(buffer, c);
		WRITE_TO_BUFFER(buffer, w);
		WRITE_TO_BUFFER(buffer, h);
		//写入整体数据
		buffer.insert(buffer.end(),
			reinterpret_cast<const char*>(tdata.data()),
			reinterpret_cast<const char*>(tdata.data()) + tdata.size() * sizeof(float));
	}
	Tensor3D Neural::ReadTensor3D(const std::vector<char>& buffer, int32_t& offset) {
		int32_t c, w, h;
		PARSE_BUFFER(buffer, offset, c);
		PARSE_BUFFER(buffer, offset, w);
		PARSE_BUFFER(buffer, offset, h);
		int32_t floatCount = static_cast<int32_t>(c) * w * h;
		int32_t dataSize = floatCount * sizeof(float);
		Tensor3D tensor(c, w, h);
		const float* src = reinterpret_cast<const float*>(buffer.data() + offset);
		for (int32_t i = 0; i < floatCount; ++i) {
			int32_t channel = i / (w * h);
			int32_t y = (i % (w * h)) / w;
			int32_t x = (i % (w * h)) % w;
			tensor.At(channel, y, x) = src[i];
		}
		offset += dataSize;
		return tensor;
	}
	bool Neural::WriteToBinaryFile(const std::string& filename, const std::vector<char>& buffer) {
		std::ofstream ofs(filename, std::ios::binary);
		if (!ofs) {
			Log::Debug("Failed to open file: " + filename);
			return false;
		}
		ofs.write(buffer.data(), buffer.size());
		if (!ofs) {
			Log::Debug("Failed to write data to file");
			return false;
		}
		Log::Debug("Successfully wrote " + std::to_string(buffer.size()) + " bytes to " + filename);
		return true;
	}
	bool Neural::ReadFromBinaryFile(const std::string& filename, std::vector<char>& buffer) {
		std::ifstream ifs(filename, std::ios::binary | std::ios::ate);
		if (!ifs) {
			Log::Debug("Failed to open file: " + filename);
			return false;
		}
		std::streamsize size = ifs.tellg();
		if (size <= 0) {
			Log::Debug("File is empty: " + filename);
			return false;
		}
		ifs.seekg(0, std::ios::beg);
		buffer.resize(static_cast<size_t>(size));
		ifs.read(buffer.data(), size);
		if (!ifs) {
			Log::Debug("Failed to read data from file");
			return false;
		}
		Log::Debug("Successfully read " + std::to_string(size) + " bytes from " + filename);
		return true;
	}
	void Neural::Train(std::vector<std::shared_ptr<Sample>>& samples, int32_t maxEpoch) {
		int32_t batch = 16;//32;
		int32_t steps = static_cast<int32_t>(std::ceil(static_cast<double>(samples.size()) / batch));
		float lr = 0.03f;
		for (int32_t epoch = 0; epoch < maxEpoch; ++epoch) {
			std::shuffle(samples.begin(), samples.end(), *g.get());
			float epochLoss = 0.0f;
			for (int32_t step = 0; step < steps; ++step) {
				int32_t start = step * batch;
				int32_t end = (step + 1) * batch;
				std::vector<std::shared_ptr<Sample>> batchSamples(samples.begin() + start, samples.begin() + (end
					> samples.size() ? samples.size() : end));
				float batchloss = TrainBatch(batchSamples,lr);
				epochLoss += batchloss;
				Log::Debug(std::format("epoch={}/{},step={}/{},batch={},lr={},batchloss={}", epoch + 1, maxEpoch, step + 1, steps, batchSamples.size(), lr, batchloss));
				std::this_thread::sleep_for(std::chrono::milliseconds(10));
			}
			epochLoss = epochLoss / steps;
			Log::Debug(std::format("epoch={}/{},lr={},epochLoss={}", epoch + 1, maxEpoch, lr,epochLoss));
		}

	}
	void Neural::GetNeural(std::vector<NeuralBuild>& builds, std::vector<std::any>& cores) {
		builds.resize(neural.size());
		cores.resize(neural.size());
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (layer == nullptr) continue;
			builds[i] = layer->GetNeuralBuild();
			if (layer->GetNeuralType() == NeuralType::Conv2D) {
				Conv2D* conv2d = dynamic_cast<Conv2D*>(layer);
				cores[i] = std::make_pair(conv2d->GetKernels(), conv2d->GetBias());
			}
			else if (layer->GetNeuralType() == NeuralType::Linear) {
				Linear* linear = dynamic_cast<Linear*>(layer);
				cores[i] = std::make_pair(linear->GetW(), linear->GetB());
			}
		}
	}
	bool Neural::SaveModel(const std::string& filename) {
		//*.dlm
		std::vector<NeuralBuild> builds;
		std::vector<std::any> cores;
		GetNeural(builds,cores);
		if (builds.size() != cores.size()) {
			Log::Debug(std::format("Model save failed, size mismatch,builds size:{},cores size:{}", builds.size(), cores.size()));
			return false;
		}
		std::vector<char> buffer;
		ModelHeader header;//写入模型的头数据
		WRITE_TO_BUFFER(buffer, header);
		int32_t buildSize = builds.size();
		WRITE_TO_BUFFER(buffer, buildSize);
		WRITE_TO_BUFFER(buffer, inputShape);
		//写入模型文件
		for (int32_t i = 0; i < builds.size(); ++i) {
			const NeuralBuild& build = builds[i];
			const std::any& core = cores[i];
			int32_t type = static_cast<int32_t>(build.type);
			//先写入类别
			WRITE_TO_BUFFER(buffer, type);
			WRITE_TO_BUFFER(buffer, build.c);
			WRITE_TO_BUFFER(buffer, build.w);
			WRITE_TO_BUFFER(buffer, build.h);
			//bias kernels
			//判断需要写入超参的网络
			if (build.type == NeuralType::Conv2D) {
				const auto& data = std::any_cast<std::pair<std::vector<Tensor3D>, Tensor3D>>(core);
				//先存储卷积核
				const std::vector<Tensor3D>& kernels = data.first;// N , M , 3 ,3 
				int32_t ksize = kernels.size();
				WRITE_TO_BUFFER(buffer, ksize);
				for (int32_t j = 0; j < kernels.size(); ++j) {
					WriteTensor3D(kernels[j],buffer);
				}
				WriteTensor3D(data.second, buffer);
			}
			else if (build.type == NeuralType::Linear) {
				const auto& data = std::any_cast<std::pair<Tensor3D, Tensor3D>>(core);
				WriteTensor3D(data.first, buffer);
				WriteTensor3D(data.second, buffer);
			}
		}
		return WriteToBinaryFile(filename,buffer);
	}
}