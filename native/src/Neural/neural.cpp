#include <cmath>
#include <format>
#include <fstream>
#include <algorithm>
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
#include <exception>
#include <stdexcept>
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
		bestValLoss = 1.0f;
		bestCharAcc = 0.0f;
		bestLabelAcc = 0.0f;
		bestEpoch = 0;
		noImproveEpoch = 0;
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
	bool Neural::Predict(const Tensor3D& input, std::array<int32_t, 4>& array,Tensor3D& output) {
		if (inputShape.c != input.Channel() || inputShape.w != input.Width() || inputShape.h != input.Height()) {
			Log::Debug(std::format("Model parameter mismatch.model shape:[{},{},{}],input shape:[{},{},{}].",
				inputShape.c, inputShape.w, inputShape.h, input.Channel(), input.Width(), input.Height()));
			return false;
		}
		Tensor3D tensor3D = Predict(input);
		output = tensor3D;
		array = TensorToLabel(tensor3D);
		return true;
	}
	bool Neural::InitFromModel(const std::string& filename) {
		Tensor3D tensor3D;
		std::vector<char> buffer;
		if (!ReadFromBinaryFile(filename, buffer)) {
			Log::Debug("Failed to load the binary file.");
			return false;
		}
		int32_t offset = 0;
		ModelHeader header;
		PARSE_BUFFER(buffer, offset, header.magic);
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
		int32_t buildSize = 0;
		PARSE_BUFFER(buffer, offset, buildSize);
		builds.resize(buildSize);
		cores.resize(buildSize);
		TensorShape shape;
		PARSE_BUFFER(buffer, offset, shape.c);
		PARSE_BUFFER(buffer, offset, shape.w);
		PARSE_BUFFER(buffer, offset, shape.h);
		for (int32_t i = 0; i < buildSize; ++i) {
			int32_t type = 0;
			int32_t c = 0;
			int32_t w = 0;
			int32_t h = 0;
			PARSE_BUFFER(buffer, offset, type);
			PARSE_BUFFER(buffer, offset, c);
			PARSE_BUFFER(buffer, offset, w);
			PARSE_BUFFER(buffer, offset, h);
			builds[i] = NeuralBuild((NeuralType)type, c, w, h);
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
		inputShape = shape;
		SetBuilds(builds);
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (layer->GetNeuralType() == NeuralType::Conv2D) {
				const auto& data = std::any_cast<std::pair<std::vector<Tensor3D>, Tensor3D>>(cores[i]);
				Conv2D* conv2d = dynamic_cast<Conv2D*>(layer);
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
		return true;
	}
	std::array<int32_t, 4> Neural::TensorToLabel(const Tensor3D& input) {
		if (input.Channel() != 1 || input.Width() != 10 || input.Height() != 4) {
			Log::Debug("tensor to label parse error.");
			return std::array<int32_t, 4>();
		}
		std::array<int32_t, 4> array;
		for (int32_t y = 0; y < input.Height(); ++y) {
			float max = std::numeric_limits<float>::lowest();
			for (int32_t x = 0; x < input.Width(); ++x) {
				float value = input.Get(0,y,x);
				if (value > max) {
					array[y] = x;
					max = value;
				}
			}
		}
		return array;
	}
	Tensor3D Neural::Predict(const Tensor3D& input) {
		Tensor3D tensor3d = input;
		for (int32_t j = 0; j < neural.size(); ++j) {
			Layer* layer = neural[j];
			if (!layer) continue;
			tensor3d = layer->Forward(tensor3d);
		}
		return tensor3d;
	}
	float Neural::TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples, float lr) {
		if (samples.size() <= 0) return 0.0f;
		float totalLoss = TrainBatchNoUpdate(samples, samples.size() <= 8);
		float batchLoss = totalLoss / (float)samples.size();
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (!layer) continue;
			layer->Update(lr, samples.size());
		}
		return batchLoss;
	}
	float Neural::TrainBatchParallel(const std::vector<std::shared_ptr<Sample>>& samples, float lr, int32_t threadCount) {
		if (samples.size() <= 0) return 0.0f;
		if (threadCount <= 1 || samples.size() == 1) return TrainBatch(samples, lr);
		int32_t workerCount = std::min(threadCount, static_cast<int32_t>(samples.size()));
		if (workerCount <= 1) return TrainBatch(samples, lr);

		std::vector<NeuralBuild> builds;
		std::vector<std::any> cores;
		GetNeural(builds, cores);

		std::vector<std::vector<std::shared_ptr<Sample>>> chunks(workerCount);
		size_t begin = 0;
		size_t baseSize = samples.size() / workerCount;
		size_t remainder = samples.size() % workerCount;
		for (int32_t i = 0; i < workerCount; ++i) {
			size_t chunkSize = baseSize + (i < remainder ? 1 : 0);
			chunks[i].insert(chunks[i].end(), samples.begin() + begin, samples.begin() + begin + chunkSize);
			begin += chunkSize;
		}

		std::vector<std::unique_ptr<Neural>> workers(workerCount);
		for (int32_t i = 0; i < workerCount; ++i) {
			workers[i] = std::make_unique<Neural>(inputShape, builds);
			workers[i]->SetCores(cores);
		}

		std::vector<float> totalLosses(workerCount, 0.0f);
		std::vector<std::exception_ptr> exceptions(workerCount, nullptr);
		std::vector<std::thread> threads;
		threads.reserve(workerCount);
		for (int32_t i = 0; i < workerCount; ++i) {
			threads.emplace_back([&, i]() {
				try {
					totalLosses[i] = workers[i]->TrainBatchNoUpdate(chunks[i], false);
				}
				catch (...) {
					exceptions[i] = std::current_exception();
				}
			});
		}
		for (std::thread& thread : threads) {
			thread.join();
		}
		for (int32_t i = 0; i < workerCount; ++i) {
			if (exceptions[i]) {
				for (auto& worker : workers) {
					if (worker) worker->Crear();
				}
				std::rethrow_exception(exceptions[i]);
			}
		}

		ClearGrad();
		for (const auto& worker : workers) {
			AccumulateGradFrom(*worker);
		}
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (!layer) continue;
			layer->Update(lr, samples.size());
		}
		for (auto& worker : workers) {
			if (worker) worker->Crear();
		}

		float totalLoss = 0.0f;
		for (float value : totalLosses) {
			totalLoss += value;
		}
		return totalLoss / (float)samples.size();
	}
	float Neural::TrainBatchNoUpdate(const std::vector<std::shared_ptr<Sample>>& samples, bool debugBatch) {
		float totalLoss = 0.0f;
		for (int32_t i = 0; i < samples.size(); ++i) {
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
			for (int32_t j = neural.size() - 1; j >= 0; --j) {
				Layer* layer = neural[j];
				if (!layer) continue;
				tensor3d = layer->Backward(tensor3d, *sample->Target());
			}
		}
		return totalLoss;
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
	void Neural::SetCores(const std::vector<std::any>& cores) {
		for (int32_t i = 0; i < neural.size() && i < cores.size(); ++i) {
			Layer* layer = neural[i];
			if (!layer) continue;
			if (layer->GetNeuralType() == NeuralType::Conv2D) {
				const auto& data = std::any_cast<const std::pair<std::vector<Tensor3D>, Tensor3D>&>(cores[i]);
				Conv2D* conv2d = dynamic_cast<Conv2D*>(layer);
				conv2d->SetKernels(data.first);
				conv2d->SetBias(data.second);
			}
			else if (layer->GetNeuralType() == NeuralType::Linear) {
				const auto& data = std::any_cast<const std::pair<Tensor3D, Tensor3D>&>(cores[i]);
				Linear* linear = dynamic_cast<Linear*>(layer);
				linear->SetW(data.first);
				linear->SetB(data.second);
			}
		}
	}
	void Neural::ClearGrad() {
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			if (!layer) continue;
			layer->ClearGrad();
		}
	}
	void Neural::AccumulateGradFrom(const Neural& other) {
		if (neural.size() != other.neural.size()) {
			throw std::invalid_argument("Neural layer size mismatch when accumulating gradients.");
		}
		for (int32_t i = 0; i < neural.size(); ++i) {
			Layer* layer = neural[i];
			Layer* otherLayer = other.neural[i];
			if (!layer || !otherLayer) continue;
			if (layer->GetNeuralType() != otherLayer->GetNeuralType()) {
				throw std::invalid_argument("Neural layer type mismatch when accumulating gradients.");
			}
			layer->AccumulateGrad(*otherLayer);
		}
	}
	void Neural::WriteTensor3D(const Tensor3D& tensor, std::vector<char>& buffer) {
		const std::vector<float>& tdata = tensor.Data();
		int32_t c = tensor.Channel();
		int32_t w = tensor.Width();
		int32_t h = tensor.Height();
		WRITE_TO_BUFFER(buffer, c);
		WRITE_TO_BUFFER(buffer, w);
		WRITE_TO_BUFFER(buffer, h);
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
	void Neural::Train(const std::string& modelPath,std::vector<std::string>& files, int32_t maxEpoch, int32_t batch, float lr) {
		if (files.size() <= 0) {
			Log::Debug("No training samples provided.");
			return;
		}
		std::shuffle(files.begin(), files.end(), *g.get());
		int32_t size20 = static_cast<size_t>(files.size() * 0.2);
		if (size20 == 0 && !files.empty()) size20 = 1;
		std::vector<std::string> validates(files.begin(), files.begin() + size20);
    	std::vector<std::string> trains(files.begin() + size20, files.end());
		int32_t steps = static_cast<int32_t>(std::ceil(static_cast<double>(trains.size()) / batch));
		for (int32_t epoch = 0; epoch < maxEpoch; ++epoch) {
			std::shuffle(trains.begin(), trains.end(), *g.get());
			float epochLoss = 0.0f;
			int32_t epochSampleCount = 0;
			for (int32_t step = 0; step < steps; ++step) {
				int32_t start = step * batch;
				int32_t end = (step + 1) * batch;
				
				std::vector<std::string> batchFiles(trains.begin() + start, trains.begin() + (end
					> trains.size() ? trains.size() : end));
				std::vector<std::shared_ptr<Sample>> batchSamples = Sample::Load(batchFiles);
				float batchloss = TrainBatchParallel(batchSamples, lr);
				epochLoss += batchloss * batchSamples.size();
				epochSampleCount += batchSamples.size();
				Log::Debug(std::format("epoch={}/{},step={}/{},batch={},lr={},batchloss={}", epoch + 1, maxEpoch, step + 1, steps, batchSamples.size(), lr, batchloss));
				std::this_thread::sleep_for(std::chrono::milliseconds(10));
			}
			epochLoss = epochSampleCount > 0 ? epochLoss / epochSampleCount : 0.0f;
			Log::Debug(std::format("epoch={}/{},lr={},epochLoss={}", epoch + 1, maxEpoch, lr,epochLoss));
			float valLoss = 0.0f;
			float charAcc = 0.0f;
			float labelAcc = 0.0f;
			//数据验证
			Validate(validates, valLoss, charAcc, labelAcc);
			if (epoch == 0) {
				bestLabelAcc = labelAcc;
				bestCharAcc = charAcc;
				bestValLoss = valLoss;
				bestEpoch = epoch;
				continue;
			} 
			if (labelAcc > bestLabelAcc) {
				bestLabelAcc = labelAcc;
				bestCharAcc = charAcc;
				bestValLoss = valLoss;
				bestEpoch = epoch;
				noImproveEpoch = 0;
				//存储更好模型
				Log::Debug("Have found a better model.");
				SaveModel(modelPath);
			}
			else {
				noImproveEpoch += 1;
			}
			if (noImproveEpoch == 5) {
				lr *= 0.5;
			}
			if (noImproveEpoch >= 10) {
				break;
			}
		}
		Log::Debug("Training ends.");
	}

	void Neural::Validate(std::vector<std::string>& files, float& valLoss, float& charAcc, float& labelAcc) {
		if(files.size() <= 0) {
			Log::Debug("No validation samples provided.");
			return;
		}
		valLoss = 0.0f;
		charAcc = 0.0f;
		labelAcc = 0.0f;
		int32_t sampleCount = 0;
		int32_t batch = 64;
		int32_t steps = static_cast<int32_t>(std::ceil(static_cast<double>(files.size()) / batch));
		for (int32_t step = 0; step < steps; ++step) {
			int32_t start = step * batch;
			int32_t end = (step + 1) * batch;
				std::vector<std::string> batchFiles(files.begin() + start, files.begin() + (end
			> files.size() ? files.size() : end));
			std::vector<std::shared_ptr<Sample>> batchSamples = Sample::Load(batchFiles);
			sampleCount+= batchSamples.size();
			for (int32_t j = 0; j < batchSamples.size(); ++j) {
				const std::shared_ptr<Sample>& batchSample = batchSamples[j];
				std::array<int32_t, 4> array;
				const std::array<int32_t, 4>* target = batchSample->Target();
				Tensor3D output;
				Predict(*batchSample->Data(), array, output);
				float loss = this->loss.Forward(output,*target);
				int32_t number = 0;
				for (int32_t index = 0; index < 4; ++index) {
					if(target->at(index) == array.at(index)) {
						++number;
					}
				}	
				charAcc += (float)number / 4.0f;
				labelAcc += (number == 4) ? 1.0f : 0.0f;
				valLoss += loss;
			}
			
		}
		if(sampleCount <= 0) {
			Log::Debug("No valid samples found for validation.");
			return;
		}
		charAcc = charAcc / sampleCount;
		labelAcc = labelAcc / sampleCount;
		valLoss = valLoss / sampleCount;
		Log::Debug(std::format("Prediction ends.charAcc:{},labelAcc:{},valLoss:{}", charAcc, labelAcc, valLoss));
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
		ModelHeader header;
		WRITE_TO_BUFFER(buffer, header);
		int32_t buildSize = builds.size();
		WRITE_TO_BUFFER(buffer, buildSize);
		WRITE_TO_BUFFER(buffer, inputShape);
		for (int32_t i = 0; i < builds.size(); ++i) {
			const NeuralBuild& build = builds[i];
			const std::any& core = cores[i];
			int32_t type = static_cast<int32_t>(build.type);

			WRITE_TO_BUFFER(buffer, type);
			WRITE_TO_BUFFER(buffer, build.c);
			WRITE_TO_BUFFER(buffer, build.w);
			WRITE_TO_BUFFER(buffer, build.h);
			//bias kernels
			if (build.type == NeuralType::Conv2D) {
				const auto& data = std::any_cast<std::pair<std::vector<Tensor3D>, Tensor3D>>(core);
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
