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
#include <thread>
#include <chrono>
namespace DeepLr::Neural {
	std::shared_ptr<std::mt19937> Neural::g = std::make_shared<std::mt19937>(42);
	Neural::Neural(const std::vector<NeuralBuild>& builds) {
		neural.resize(builds.size());
		int32_t lastC = 1;
		int32_t lastH = 1;
		for (int32_t i = 0; i < builds.size(); ++i) {
			auto& build = builds[i];
			neural[i] = nullptr;
			if (build.type == NeuralType::Conv2D) neural[i] = new Conv2D(build.c, lastC);
			else if(build.type == NeuralType::RelU)neural[i] = new Relu();
			else if (build.type == NeuralType::MaxPool)neural[i] = new MaxPool();
			else if (build.type == NeuralType::Flatten)neural[i] = new Flatten();
			else if (build.type == NeuralType::Linear)neural[i] = new Linear(lastH,build.h);
			else if (build.type == NeuralType::SoftMax)neural[i] = new SoftMax(build.w,build.h);
			lastC = build.c;
			lastH = build.h;
		}
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
		return std::make_shared<Neural>(builds);
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
				tensor3d = layer->Forward(tensor3d, *sample->Target());
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
				std::this_thread::sleep_for(std::chrono::milliseconds(30));
			}
			epochLoss = epochLoss / steps;
			Log::Debug(std::format("epoch={}/{},lr={},epochLoss={}", epoch + 1, maxEpoch, lr,epochLoss));
		}

	}
}