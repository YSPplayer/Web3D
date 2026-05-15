#include <cmath>
#include <format>
#include "neural.h"
#include "conv2d.h"
#include "relu.h"
#include "maxpool.h"
#include "flatten.h"
#include "linear.h"
#include "softmax.h"
#include "../log.h"
namespace DeepLr::Neural {
	std::shared_ptr<std::mt19937> Neural::g = std::make_shared<std::mt19937>(42);
	Neural::Neural(const std::vector<NeuralBuild>& builds) {
		neural.resize(builds.size());
		for (int32_t i = 0; i < builds.size(); ++i) {
			auto& build = builds[i];
			neural[i] = nullptr;
			if (build.type == NeuralType::Conv2D) neural[i] = new Conv2D(build.c);
			else if(build.type == NeuralType::RelU)neural[i] = new Relu();
			else if (build.type == NeuralType::MaxPool)neural[i] = new MaxPool();
			else if (build.type == NeuralType::Flatten)neural[i] = new Flatten();
			else if (build.type == NeuralType::Linear)neural[i] = new Linear();
			else if (build.type == NeuralType::SoftMax)neural[i] = new SoftMax();
		}
	}
	void Neural::BuildNeural() {
		Neural* n = new Neural({ 
			NeuralBuild(NeuralType::Conv2D, 8),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,16),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,24),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Conv2D,32),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::MaxPool),
			NeuralBuild(NeuralType::Flatten),
			NeuralBuild(NeuralType::Linear,64),
			NeuralBuild(NeuralType::RelU),
			NeuralBuild(NeuralType::Linear,40),
			NeuralBuild(NeuralType::SoftMax),
		});
	}
	float Neural::TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples, float lr) {
		if (samples.size() <= 0) return 0.0f;
		float totalLoss = 0.0f;
		float batchLoss = 0.0f;
		//向前传播
		for (int32_t i = 0; i < samples.size(); ++i) { //批量训练
			const auto& sample = samples.at(i);
			Tensor3D tensor3d = *sample->Data();
			for (int32_t j = 0; j < neural.size(); ++j) {
				Layer* layer = neural[j];
				if (!layer) continue;
				tensor3d = layer->Forward(tensor3d, *sample->Target());
			}
			totalLoss += loss.Forward(tensor3d, *sample->Target());
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
			layer->Update(lr);
		}
		return batchLoss;
	}
	void Neural::Train(std::vector<std::shared_ptr<Sample>>& samples, int32_t maxEpoch) {
		int32_t batch = 32;
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
				Log::Debug(std::format("epoch={}/{},step={}/{},batch={},lr={},batchloss={}", epoch, maxEpoch, step, steps, batchSamples.size(), lr, batchloss));
			}
			epochLoss = epochLoss / steps;
			Log::Debug(std::format("epoch={}/{},lr={},epochLoss={}", epoch, maxEpoch, lr,epochLoss));
		}

	}
}